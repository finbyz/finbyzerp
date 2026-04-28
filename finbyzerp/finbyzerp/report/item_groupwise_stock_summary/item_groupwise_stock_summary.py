from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

from erpnext.accounts.report.item_wise_purchase_register.item_wise_purchase_register import execute as purchase_execute
from erpnext.accounts.report.item_wise_sales_register.item_wise_sales_register import execute as sales_execute


# ================= MAIN =================

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


# ================= DATA =================

def get_data(filters):
    item_group = get_item_group(filters)

    if not item_group:
        return []

    item_group = filter_item_group(item_group)
    out = prepare_data(item_group)
    return get_final_out(out)


# ================= GST =================

def merge_accounts(account_list):
    merged = frappe._dict({
        "cgst_account": [],
        "sgst_account": [],
        "igst_account": [],
        "cess_account": [],
        "tcs_account": [],
        "export_reverse_charge_account": []
    })

    for acc in account_list:
        for key in merged:
            if acc.get(key):
                merged[key].append(acc.get(key))

    return merged


def get_tax_amount(tax, account_list):
    total = 0
    for acc in account_list or []:
        total += flt(tax.get(acc) or tax.get(acc + "_amount") or 0)
    return total


def get_item_map(filters):

    # ===== GST NORMAL
    gst_accounts_list = frappe.get_all(
        "GST Account",
        filters={
            "parent": "GST Settings",
            "company": filters.company,
            "account_type": ["in", ["Input", "Output"]]
        },
        fields=["cgst_account", "sgst_account", "igst_account",
                "cess_account", "tcs_account", "export_reverse_charge_account"]
    )

    if not gst_accounts_list:
        frappe.throw(f"Define GST Input/Output Accounts for {filters.company}")

    # ===== GST REVERSE
    gst_reverse_list = frappe.get_all(
        "GST Account",
        filters={
            "parent": "GST Settings",
            "company": filters.company,
            "account_type": ["in", ["Purchase Reverse Charge", "Sales Reverse Charge"]]
        },
        fields=["cgst_account", "sgst_account", "igst_account",
                "cess_account", "tcs_account", "export_reverse_charge_account"]
    )

    if not gst_reverse_list:
        frappe.throw(f"Define Reverse Charge GST Accounts for {filters.company}")

    accounts = merge_accounts(gst_accounts_list)
    reverse_accounts = merge_accounts(gst_reverse_list)

    purchase_data = purchase_execute(filters)
    sales_data = sales_execute(filters)

    item_map = {}
    item_tax_map = {}

    # ===== PURCHASE
    if filters.get("purchase") or not filters.get("sales"):
        for tax in purchase_data[1]:

            tax_amt = (
                get_tax_amount(tax, accounts.cgst_account) +
                get_tax_amount(tax, accounts.sgst_account) +
                get_tax_amount(tax, accounts.igst_account) +
                get_tax_amount(tax, accounts.cess_account) +
                get_tax_amount(tax, accounts.tcs_account) +
                get_tax_amount(tax, accounts.export_reverse_charge_account) +

                get_tax_amount(tax, reverse_accounts.cgst_account) +
                get_tax_amount(tax, reverse_accounts.sgst_account) +
                get_tax_amount(tax, reverse_accounts.igst_account) +
                get_tax_amount(tax, reverse_accounts.cess_account) +
                get_tax_amount(tax, reverse_accounts.tcs_account) +
                get_tax_amount(tax, reverse_accounts.export_reverse_charge_account)
            )

            item_code = tax.get("item_code")

            item_map[item_code] = item_map.get(item_code, 0) + (tax.get("amount") or 0)
            item_tax_map[item_code] = item_tax_map.get(item_code, 0) + tax_amt

    # ===== SALES
    if filters.get("sales") or not filters.get("purchase"):
        for tax in sales_data[1]:

            tax_amt = (
                get_tax_amount(tax, accounts.cgst_account) +
                get_tax_amount(tax, accounts.sgst_account) +
                get_tax_amount(tax, accounts.igst_account) +
                get_tax_amount(tax, accounts.cess_account) +
                get_tax_amount(tax, accounts.tcs_account) +
                get_tax_amount(tax, accounts.export_reverse_charge_account)
            )

            item_code = tax.get("item_code")

            item_map[item_code] = item_map.get(item_code, 0) + (tax.get("amount") or 0)
            item_tax_map[item_code] = item_tax_map.get(item_code, 0) + tax_amt

    return item_map, item_tax_map


# ================= ITEM GROUP =================

def get_item_group(filters):

    item_group = frappe.db.sql("""
        SELECT name, parent_item_group, 1 as is_group
        FROM `tabItem Group`
        ORDER BY lft
    """, as_dict=True)

    items = frappe.db.sql("""
        SELECT item_code, item_name, item_group as parent_item_group, 0 as is_group
        FROM `tabItem`
    """, as_dict=True)

    item_map, item_tax_map = get_item_map(filters)

    for d in items:
        d.name = d.item_code
        d.net_amount = item_map.get(d.item_code) or 0
        d.tax_amount = item_tax_map.get(d.item_code) or 0
        d.total_amount = d.net_amount + d.tax_amount

    return item_group + items


# ================= TREE =================

def filter_item_group(item_group):

    parent_map = {}
    result = []

    for d in item_group:
        parent_map.setdefault(d.parent_item_group or None, []).append(d)

    def build(parent, level):
        for child in parent_map.get(parent, []):
            child.indent = level
            result.append(child)
            build(child.name, level + 1)

    build(None, 0)
    return result


def prepare_data(item_group):

    data = []

    for d in item_group:
        data.append(frappe._dict({
            "item_group": d.get("item_name") or d.name,
            "parent_item_group": d.parent_item_group,
            "indent": d.indent,
            "net_amount": flt(d.get("net_amount")),
            "tax_amount": flt(d.get("tax_amount")),
            "total_amount": flt(d.get("total_amount")),
            "is_group": d.is_group
        }))

    return data


def get_final_out(out):

    group_map = {d.item_group: d for d in out if d.is_group}

    # bottom-up aggregation
    for row in sorted(out, key=lambda x: x.indent, reverse=True):
        if row.parent_item_group and row.parent_item_group in group_map:
            parent = group_map[row.parent_item_group]

            parent.net_amount += row.net_amount
            parent.tax_amount += row.tax_amount
            parent.total_amount += row.total_amount

    return out


# ================= COLUMNS =================

def get_columns():
    return [
        {"fieldname": "item_group", "label": "Item Group", "fieldtype": "Data", "width": 350},
        {"fieldname": "net_amount", "label": "Net Amount", "fieldtype": "Currency", "width": 150},
        {"fieldname": "tax_amount", "label": "Tax Amount", "fieldtype": "Currency", "width": 150},
        {"fieldname": "total_amount", "label": "Total Amount", "fieldtype": "Currency", "width": 150},
    ]
