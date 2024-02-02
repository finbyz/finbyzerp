
from frappe import _

import frappe
from frappe.model.meta import get_field_precision

from erpnext import get_default_currency
from erpnext.accounts.report.non_billed_report import get_ordered_to_be_billed_data


def execute(filters=None):
	columns = get_column()
	args = get_args()
	data = get_ordered_to_be_billed_data(args)
	return columns, data

def get_ordered_to_be_billed_data(args):
	doctype, party = args.get("doctype"), args.get("party")
	child_tab = doctype + " Item"
	precision = (
		get_field_precision(
			frappe.get_meta(child_tab).get_field("billed_amt"), currency=get_default_currency()
		)
		or 2
	)

	project_field = get_project_field(doctype, party)

	return frappe.db.sql(
		"""
		Select
			`{parent_tab}`.name, `{parent_tab}`.{date_field},
			`{parent_tab}`.{party}, `{parent_tab}`.{party}_name,
			`{child_tab}`.item_code,
			`{child_tab}`.base_amount,
			(`{child_tab}`.billed_amt * ifnull(`{parent_tab}`.conversion_rate, 1)),
			(`{child_tab}`.base_rate * ifnull(`{child_tab}`.returned_qty, 0)),
			(`{child_tab}`.base_amount -
			(`{child_tab}`.billed_amt * ifnull(`{parent_tab}`.conversion_rate, 1)) -
			(`{child_tab}`.base_rate * ifnull(`{child_tab}`.returned_qty, 0))),
			`{child_tab}`.item_name, `{child_tab}`.description,
			{project_field}, `{parent_tab}`.company,
			`{child_tab}`.warehouse
		from
			`{parent_tab}`, `{child_tab}`
		where
			`{parent_tab}`.name = `{child_tab}`.parent and `{parent_tab}`.docstatus = 1
			and `{parent_tab}`.status not in ('Closed', 'Completed')
			and `{child_tab}`.amount > 0
			and (`{child_tab}`.base_amount -
			round(`{child_tab}`.billed_amt * ifnull(`{parent_tab}`.conversion_rate, 1), {precision}) -
			(`{child_tab}`.base_rate * ifnull(`{child_tab}`.returned_qty, 0))) > 0
		order by
			`{parent_tab}`.{order} {order_by}
		""".format(
			parent_tab="tab" + doctype,
			child_tab="tab" + child_tab,
			precision=precision,
			party=party,
			date_field=args.get("date"),
			project_field=project_field,
			order=args.get("order"),
			order_by=args.get("order_by"),
		)
	)


def get_project_field(doctype, party):
	if party == "supplier":
		doctype = doctype + " Item"
	return "`tab%s`.project" % (doctype)

def get_column():
	return [
		{
			"label": _("Purchase Receipt"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Purchase Receipt",
			"width": 160,
		},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 120,
		},
		{"label": _("Supplier Name"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 120},
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120,
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 100,
			"options": "Company:company:default_currency",
		},
		{
			"label": _("Billed Amount"),
			"fieldname": "billed_amount",
			"fieldtype": "Currency",
			"width": 100,
			"options": "Company:company:default_currency",
		},
		{
			"label": _("Returned Amount"),
			"fieldname": "returned_amount",
			"fieldtype": "Currency",
			"width": 120,
			"options": "Company:company:default_currency",
		},
		{
			"label": _("Pending Amount"),
			"fieldname": "pending_amount",
			"fieldtype": "Currency",
			"width": 120,
			"options": "Company:company:default_currency",
		},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 120},
		{"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 120},
		{
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 120,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 120,
		},
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 120,
		},
	]


def get_args():
	return {
		"doctype": "Purchase Receipt",
		"party": "supplier",
		"date": "posting_date",
		"order": "name",
		"order_by": "desc",
	}
