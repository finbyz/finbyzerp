# Copyright (c) 2025, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import copy
from collections import defaultdict

import frappe
from frappe import _
from frappe.query_builder.functions import CombineDatetime, Sum
from frappe.utils import cint, flt, get_datetime
from erpnext.stock.stock_ledger import get_previous_sle

from erpnext.stock.doctype.inventory_dimension.inventory_dimension import get_inventory_dimensions
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos
from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import get_stock_balance_for
from erpnext.stock.doctype.warehouse.warehouse import apply_warehouse_filter
from erpnext.stock.utils import (
    is_reposting_item_valuation_in_progress,
    update_included_uom_in_report,
)


def execute(filters=None):
    is_reposting_item_valuation_in_progress()
    include_uom = filters.get("include_uom")
    columns = get_columns(filters)
    items = get_items(filters)
    sl_entries = get_stock_ledger_entries(filters, items)
    item_details = get_item_details(items, sl_entries, include_uom)

    # Get precision for calculations
    precision = cint(frappe.db.get_single_value("System Settings", "float_precision"))

    # Initialize opening balance maps
    opening_map = defaultdict(float)
    opening_value_map = defaultdict(float)
    opening_rate_map = defaultdict(float)
    running_bal = defaultdict(float)
    running_value = defaultdict(float)

    # Compute opening balances from previous SLEs
    if filters.get("from_date"):
        args = [filters.get("from_date")]
        item_condition = ""
        if items:
            item_condition = " AND item_code IN ({})".format(", ".join(["%s"] * len(items)))
            args.extend(items)

        if filters.get("warehouse"):
            item_condition += " AND warehouse = %s"
            args.append(filters.get("warehouse"))

        if filters.get("company"):
            item_condition += " AND company = %s"
            args.append(filters.get("company"))

        prev_sles = frappe.db.sql(
            f"""
            SELECT
                item_code, warehouse, posting_date, posting_time,
                actual_qty, qty_after_transaction, voucher_type, stock_value_difference,
                voucher_no, company, stock_value, valuation_rate
            FROM `tabStock Ledger Entry`
            WHERE docstatus < 2
              AND is_cancelled = 0
              AND posting_date < %s
              {item_condition}
            ORDER BY posting_date, posting_time, creation
            """,
            tuple(args),
            as_dict=True,
        )

        for d in prev_sles:
            key = d["item_code"]
            if d.get("voucher_type") == "Stock Reconciliation":
                qty_diff = flt(d.get("qty_after_transaction")) - flt(running_bal[key])
            else:
                qty_diff = flt(d.get("actual_qty"))

            running_bal[key] += qty_diff
            running_value[key] = flt(d.get("stock_value", 0))
            
            opening_map[key] = running_bal[key]
            opening_value_map[key] = running_value[key]
            
            # Calculate opening rate
            if opening_map[key] != 0:
                opening_rate_map[key] = flt(opening_value_map[key] / opening_map[key], precision)

    # Get Sales Invoice return status
    si_nos = [sle.voucher_no for sle in sl_entries if sle.voucher_type == "Sales Invoice"]
    si_map = {}
    if si_nos:
        si_rows = frappe.get_all(
            "Sales Invoice",
            filters={"name": ["in", si_nos]},
            fields=["name", "is_return"],
        )
        si_map = {r.name: r.is_return for r in si_rows}

    # Get Purchase Invoice return status
    pi_nos = [sle.voucher_no for sle in sl_entries if sle.voucher_type == "Purchase Invoice"]
    pi_map = {}
    if pi_nos:
        pi_rows = frappe.get_all(
            "Purchase Invoice",
            filters={"name": ["in", pi_nos]},
            fields=["name", "is_return"],
        )
        pi_map = {r.name: r.is_return for r in pi_rows}

    # Get Stock Entry types
    se_nos = [sle.voucher_no for sle in sl_entries if sle.voucher_type == "Stock Entry"]
    se_map = {}
    if se_nos:
        se_rows = frappe.get_all(
            "Stock Entry",
            filters={"name": ["in", se_nos]},
            fields=["name", "stock_entry_type"],
        )
        se_map = {r.name: r.stock_entry_type for r in se_rows}

    item_wise_data = {}
    for sle in sl_entries:
        item_code = sle.item_code
        item_name = item_details[item_code].get("item_name")

        if item_code not in item_wise_data:
            item_wise_data[item_code] = {
                "item_code": item_code,
                "item_name": item_name,
                "stock_uom": item_details[item_code].get("stock_uom"),
                "item_group": item_details[item_code].get("item_group"),
                "brand": item_details[item_code].get("brand"),
                "description": item_details[item_code].get("description"),
                
                # Opening Balance
                "opening_balance": flt(opening_map.get(item_code, 0.0)),
                "opening_rate": flt(opening_rate_map.get(item_code, 0.0)),
                "opening_value": flt(opening_value_map.get(item_code, 0.0)),
                
                # Inwards (Purchase + Manufacturer)
                "inwards_qty": 0,
                "inwards_rate": 0,
                "inwards_value": 0,
                
                # Outwards (Sales + Consumption)
                "outwards_qty": 0,
                "outwards_rate": 0,
                "outwards_value": 0,
                
                # Closing Balance
                "qty_after_transaction": 0,
                "closing_rate": 0,
                "closing_value": 0,
                
                # Keep these for internal calculations
                "purchase": 0,
                "manufacturer": 0,
                "sales": 0,
                "consumption": 0,
                "warehouse": sle.warehouse,
                "batch_no": sle.batch_no,
                "serial_no": sle.serial_no,
                "project": sle.project,
            }

        # Categorize transactions based on voucher type
        if sle.voucher_type == "Purchase Receipt":
            item_wise_data[item_code]["purchase"] += flt(sle.actual_qty)
            item_wise_data[item_code]["inwards_value"] += flt(sle.stock_value_difference)
        
        elif sle.voucher_type == "Purchase Invoice":
            if not pi_map.get(sle.voucher_no):
                item_wise_data[item_code]["purchase"] += flt(sle.actual_qty)
                item_wise_data[item_code]["inwards_value"] += flt(sle.stock_value_difference)
            else:
                item_wise_data[item_code]["purchase"] += flt(sle.actual_qty)
                item_wise_data[item_code]["inwards_value"] += flt(sle.stock_value_difference)
        
        elif sle.voucher_type == "Stock Entry":
            stock_entry_type = se_map.get(sle.voucher_no)
            
            if stock_entry_type == "Manufacture":
                if sle.actual_qty > 0:
                    # Finished goods produced (Inward)
                    item_wise_data[item_code]["manufacturer"] += flt(sle.actual_qty)
                    item_wise_data[item_code]["inwards_value"] += flt(sle.stock_value_difference)
                else:
                    # Raw materials consumed (Outward)
                    item_wise_data[item_code]["consumption"] += flt(sle.actual_qty)
                    item_wise_data[item_code]["outwards_value"] += flt(sle.stock_value_difference)
        
        elif sle.voucher_type == "Delivery Note":
            item_wise_data[item_code]["sales"] += flt(sle.actual_qty)
            item_wise_data[item_code]["outwards_value"] += flt(sle.stock_value_difference)
        
        elif sle.voucher_type == "Sales Invoice":
            if not si_map.get(sle.voucher_no):
                item_wise_data[item_code]["sales"] += flt(sle.actual_qty)
                item_wise_data[item_code]["outwards_value"] += flt(sle.stock_value_difference)
            else:
                item_wise_data[item_code]["sales"] += flt(sle.actual_qty)
                item_wise_data[item_code]["outwards_value"] += flt(sle.stock_value_difference)

    # Compute final values for each item
    for item_code, row in item_wise_data.items():
        # Calculate Inwards Quantity (Purchase + Manufacturer)
        row["inwards_qty"] = flt(row["purchase"]) + flt(row["manufacturer"])
        
        # Calculate Inwards Rate (weighted average)
        if row["inwards_qty"] != 0:
            row["inwards_rate"] = flt(row["inwards_value"] / row["inwards_qty"], precision)
        
        # Calculate Outwards Quantity (Sales + Consumption) - these are negative
        row["outwards_qty"] = flt(row["sales"]) + flt(row["consumption"])
        
        # Calculate Outwards Rate (weighted average)
        if row["outwards_qty"] != 0:
            row["outwards_rate"] = flt(row["outwards_value"] / row["outwards_qty"], precision)
        
        # Calculate Closing Balance Quantity
        row["qty_after_transaction"] = (
            flt(row["opening_balance"])
            + flt(row["inwards_qty"])
            + flt(row["outwards_qty"])  # Already negative
        )
        
        # Calculate Closing Value
        row["closing_value"] = (
            flt(row["opening_value"])
            + flt(row["inwards_value"])
            + flt(row["outwards_value"])  # Already negative for outwards
        )
        
        # Calculate Closing Rate
        if row["qty_after_transaction"] != 0:
            row["closing_rate"] = flt(row["closing_value"] / row["qty_after_transaction"], precision)

    # Final data
    data = list(item_wise_data.values())

    include_zero_qty = filters.get("include_zero_qty")

    final_data = []
    for row in data:
        # skip zero qty rows when checkbox is OFF
        if not include_zero_qty and flt(row.get("qty_after_transaction")) == 0:
            continue
        final_data.append(row)

    data = final_data

    
    # Add Grand Total row
    if data:
        grand_total = {
            "item_name": "<b>Grand Total</b>",
            "stock_uom": "",
            # Leave quantity/rate columns blank; show only value aggregates
            "opening_balance": None,
            "opening_rate": None,
            "opening_value": sum(flt(row.get("opening_value", 0)) for row in data),
            "inwards_qty": None,
            "inwards_rate": None,
            "inwards_value": sum(flt(row.get("inwards_value", 0)) for row in data),
            "outwards_qty": None,
            "outwards_rate": None,
            "outwards_value": sum(flt(row.get("outwards_value", 0)) for row in data),
            "qty_after_transaction": None,
            "closing_rate": None,
            "closing_value": sum(flt(row.get("closing_value", 0)) for row in data),
        }
        data.append(grand_total)
    
    update_included_uom_in_report(columns, data, include_uom, [])

   
    custom_report_header = [
        ["Stock Balance Summary"],
        [""],
        [f"Company: {filters.get('company') or 'All'}"],
        [f"From Date: {filters.get('from_date')}"],
        [f"To Date: {filters.get('to_date')}"],
    ]
    
    # Add optional filters to header
    if filters.get("branch"):
        custom_report_header.append([f"Branch: {filters.get('branch')}"])
    
    if filters.get("warehouse"):
        custom_report_header.append([f"Warehouse: {filters.get('warehouse')}"])
    
    if filters.get("item_group"):
        custom_report_header.append([f"Item Group: {filters.get('item_group')}"])
    
    if filters.get("brand"):
        custom_report_header.append([f"Brand: {filters.get('brand')}"])
    
    if filters.get("item_code"):
        custom_report_header.append([f"Item: {filters.get('item_code')}"])
    
    custom_report_header.append([f"Include Zero Qty: {'Yes' if filters.get('include_zero_qty') else 'No'}"])
    custom_report_header.append([""])  # Empty line before data


    return columns, data,None,custom_report_header


def get_columns(filters):
    columns = [
        {
            "label": _("Particulars"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 250,
        },
        {
            "label": _("Stock UOM"),
            "fieldname": "stock_uom",
            "fieldtype": "Link",
            "options": "UOM",
            "width": 120,
        },
    ]

    for dimension in get_inventory_dimensions():
        columns.append(
            {
                "label": _(dimension.doctype),
                "fieldname": dimension.fieldname,
                "fieldtype": "Link",
                "options": dimension.doctype,
                "width": 110,
            }
        )

    columns.extend(
        [
            # Opening Balance Section
            {
                "label": _("Quantity"),
                "fieldname": "opening_balance",
                "fieldtype": "Float",
                "width": 100,
            },
            {
                "label": _("Rate"),
                "fieldname": "opening_rate",
                "fieldtype": "Currency",
                "width": 100,
                "options": "Company:company:default_currency",
            },
            {
                "label": _("Value"),
                "fieldname": "opening_value",
                "fieldtype": "Currency",
                "width": 120,
                "options": "Company:company:default_currency",
            },
            
            # Inwards Section
            {
                "label": _("Quantity"),
                "fieldname": "inwards_qty",
                "fieldtype": "Float",
                "width": 100,
            },
            {
                "label": _("Rate"),
                "fieldname": "inwards_rate",
                "fieldtype": "Currency",
                "width": 100,
                "options": "Company:company:default_currency",
            },
            {
                "label": _("Value"),
                "fieldname": "inwards_value",
                "fieldtype": "Currency",
                "width": 120,
                "options": "Company:company:default_currency",
            },
            
            # Outwards Section
            {
                "label": _("Quantity"),
                "fieldname": "outwards_qty",
                "fieldtype": "Float",
                "width": 100,
            },
            {
                "label": _("Rate"),
                "fieldname": "outwards_rate",
                "fieldtype": "Currency",
                "width": 100,
                "options": "Company:company:default_currency",
            },
            {
                "label": _("Value"),
                "fieldname": "outwards_value",
                "fieldtype": "Currency",
                "width": 120,
                "options": "Company:company:default_currency",
            },
            
            # Closing Balance Section
            {
                "label": _("Quantity"),
                "fieldname": "qty_after_transaction",
                "fieldtype": "Float",
                "width": 100,
                "convertible": "qty",
            },
            {
                "label": _("Rate"),
                "fieldname": "closing_rate",
                "fieldtype": "Currency",
                "width": 100,
                "options": "Company:company:default_currency",
            },
            {
                "label": _("Value"),
                "fieldname": "closing_value",
                "fieldtype": "Currency",
                "width": 120,
                "options": "Company:company:default_currency",
            },
        ]
    )

    return columns


def get_stock_ledger_entries(filters, items):
    from_date = get_datetime(filters.from_date + " 00:00:00")
    to_date = get_datetime(filters.to_date + " 23:59:59")

    sle = frappe.qb.DocType("Stock Ledger Entry")
    query = (
        frappe.qb.from_(sle)
        .select(
            sle.item_code,
            sle.posting_datetime.as_("date"),
            sle.warehouse,
            sle.posting_date,
            sle.posting_time,
            sle.actual_qty,
            sle.incoming_rate,
            sle.valuation_rate,
            sle.company,
            sle.voucher_type,
            sle.qty_after_transaction,
            sle.stock_value_difference,
            sle.serial_and_batch_bundle,
            sle.voucher_no,
            sle.stock_value,
            sle.batch_no,
            sle.serial_no,
            sle.project,
        )
        .where((sle.docstatus < 2) & (sle.is_cancelled == 0) & (sle.posting_datetime[from_date:to_date]))
        .orderby(sle.posting_datetime)
        .orderby(sle.creation)
    )

    inventory_dimension_fields = get_inventory_dimension_fields()
    if inventory_dimension_fields:
        for fieldname in inventory_dimension_fields:
            query = query.select(fieldname)
            if fieldname in filters and filters.get(fieldname):
                query = query.where(sle[fieldname].isin(filters.get(fieldname)))

    if items:
        query = query.where(sle.item_code.isin(items))

    for field in ["voucher_no", "project", "company"]:
        if filters.get(field) and field not in inventory_dimension_fields:
            query = query.where(sle[field] == filters.get(field))

    if filters.get("batch_no"):
        bundles = get_serial_and_batch_bundles(filters)

        if bundles:
            query = query.where(
                (sle.serial_and_batch_bundle.isin(bundles)) | (sle.batch_no == filters.batch_no)
            )
        else:
            query = query.where(sle.batch_no == filters.batch_no)
    # Branch → all warehouses
    if filters.get("branch"):
        warehouses = frappe.get_all(
            "Warehouse",
            filters={"branch": filters.get("branch")},
            pluck="name"
        )
        if warehouses:
            query = query.where(sle.warehouse.isin(warehouses))


    query = apply_warehouse_filter(query, sle, filters)

    return query.run(as_dict=True)


def get_serial_and_batch_bundles(filters):
    SBB = frappe.qb.DocType("Serial and Batch Bundle")
    SBE = frappe.qb.DocType("Serial and Batch Entry")

    query = (
        frappe.qb.from_(SBE)
        .inner_join(SBB)
        .on(SBE.parent == SBB.name)
        .select(SBE.parent)
        .where(
            (SBB.docstatus == 1)
            & (SBB.has_batch_no == 1)
            & (SBB.voucher_no.notnull())
            & (SBE.batch_no == filters.batch_no)
        )
    )

    return query.run(pluck=SBE.parent)


def get_inventory_dimension_fields():
    return [dimension.fieldname for dimension in get_inventory_dimensions()]


def get_items(filters):
    item = frappe.qb.DocType("Item")
    query = frappe.qb.from_(item).select(item.name)
    conditions = []

    if item_code := filters.get("item_code"):
        conditions.append(item.name == item_code)
    else:
        if brand := filters.get("brand"):
            conditions.append(item.brand == brand)
        if item_group := filters.get("item_group"):
            if condition := get_item_group_condition(item_group, item):
                conditions.append(condition)

    items = []
    if conditions:
        for condition in conditions:
            query = query.where(condition)
        items = [r[0] for r in query.run()]

    return items


def get_item_details(items, sl_entries, include_uom):
    item_details = {}
    if not items:
        items = list(set(d.item_code for d in sl_entries))

    if not items:
        return item_details

    item = frappe.qb.DocType("Item")
    query = (
        frappe.qb.from_(item)
        .select(item.name, item.item_name, item.description, item.item_group, item.brand, item.stock_uom)
        .where(item.name.isin(items))
    )

    if include_uom:
        ucd = frappe.qb.DocType("UOM Conversion Detail")
        query = (
            query.left_join(ucd)
            .on((ucd.parent == item.name) & (ucd.uom == include_uom))
            .select(ucd.conversion_factor)
        )

    res = query.run(as_dict=True)

    for item in res:
        item_details.setdefault(item.name, item)

    return item_details


def get_item_group_condition(item_group, item_table=None):
    item_group_details = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"], as_dict=1)
    if item_group_details:
        if item_table:
            ig = frappe.qb.DocType("Item Group")
            return item_table.item_group.isin(
                frappe.qb.from_(ig)
                .select(ig.name)
                .where(
                    (ig.lft >= item_group_details.lft)
                    & (ig.rgt <= item_group_details.rgt)
                    & (item_table.item_group == ig.name)
                )
            )
        else:
            return f"item.item_group in (select ig.name from `tabItem Group` ig \
                where ig.lft >= {item_group_details.lft} and ig.rgt <= {item_group_details.rgt} and item.item_group = ig.name)"