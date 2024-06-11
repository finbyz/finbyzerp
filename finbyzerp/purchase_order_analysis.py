import copy

import frappe
from frappe import _
from frappe.query_builder.functions import IfNull, Sum
from frappe.utils import date_diff, flt, getdate

def get_data(filters):
	po = frappe.qb.DocType("Purchase Order")
	po_item = frappe.qb.DocType("Purchase Order Item")
	pi_item = frappe.qb.DocType("Purchase Invoice Item")
	pi = frappe.qb.DocType("Purchase Invoice") # Finbyz Changes

	query = (
		frappe.qb.from_(po)
		.from_(po_item)
		.left_join(pi_item)
		.on(pi_item.po_detail == po_item.name)
		.left_join(pi) # Finbyz Changes
		.on(pi.name == pi_item.parent) # Finbyz Changes
		.select(
			po.transaction_date.as_("date"),
			po_item.schedule_date.as_("required_date"),
			po_item.project,
			po.name.as_("purchase_order"),
			po.status,
			po.supplier,
			po_item.item_code,
			po_item.qty,
			po_item.received_qty,
			(po_item.qty - po_item.received_qty).as_("pending_qty"),
			Sum(IfNull(pi_item.qty, 0)).as_("billed_qty"),
			po_item.base_amount.as_("amount"),
			(po_item.received_qty * po_item.base_rate).as_("received_qty_amount"),
			(po_item.billed_amt * IfNull(po.conversion_rate, 1)).as_("billed_amount"),
			(po_item.base_amount - (po_item.billed_amt * IfNull(po.conversion_rate, 1))).as_(
				"pending_amount"
			),
			po_item.warehouse.as_("warehouse"), # Finbyz Changes
			po.company,
			po_item.name,
		)
		.where(
			(po_item.parent == po.name) & (po.status.notin(("Stopped", "Closed"))) & (po.docstatus == 1) & (pi.docstatus == 1) # Finbyz Changes
		)
		.groupby(po_item.name)
		.orderby(po.transaction_date)
	)

	for field in ("company", "name"):
		if filters.get(field):
			query = query.where(po[field] == filters.get(field))

	if filters.get("from_date") and filters.get("to_date"):
		query = query.where(
			po.transaction_date.between(filters.get("from_date"), filters.get("to_date"))
		)

	if filters.get("status"):
		query = query.where(po.status.isin(filters.get("status")))

	if filters.get("project"):
		query = query.where(po_item.project == filters.get("project"))

	data = query.run(as_dict=True)

	return data