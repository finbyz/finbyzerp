# Copyright (c) 2013, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _, scrub

def execute(filters=None):
	filters = frappe._dict(filters) if filters else frappe._dict()
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	doctype = "Sales Invoice" if filters.doctype == "Sales" else "Purchase Invoice"

	child_doctype = doctype + " Item"

	if doctype == "Sales Invoice":
		delivery_receipt = "Delivery Note Item"
		delivery_receipt_name = "Delivery Note"
		child_dn_pr = "dn_detail"
	else:
		delivery_receipt = "Purchase Receipt Item"
		delivery_receipt_name = "Purchase Receipt"
		child_dn_pr = "pr_detail"

	# Get Invoices where delivery or receipt amount is not same or invoices without delivery or receipt
	data = frappe.db.sql(f"""
		select
			invoice.name as invoice_name, invoice_item.item_code, invoice_item.net_amount as invoice_amount,
			IFNULL(dn_pr.name, null) as name,
			IF(dn_pr.posting_date between '{filters.from_date}' and '{filters.to_date}', IFNULL(dni.net_amount,0), 0) as receipt_net_amount
		from 
			`tab{doctype}` as invoice
			JOIN `tab{child_doctype}` as invoice_item on invoice_item.parent = invoice.name
			LEFT JOIN `tab{delivery_receipt}` as dni on dni.name = invoice_item.{child_dn_pr} and dni.parent = invoice_item.{scrub(delivery_receipt_name)}
			LEFT JOIN `tab{delivery_receipt_name}` as dn_pr on dn_pr.name = invoice_item.{scrub(delivery_receipt_name)}
		where
			(invoice_item.{scrub(delivery_receipt_name)} is null or invoice_item.{scrub(delivery_receipt_name)} = '' or
			(invoice_item.{scrub(delivery_receipt_name)} is not null and round(dni.net_amount) != round(invoice_item.net_amount) and dni.docstatus = 1)) and
			invoice.update_stock = 0 and invoice.is_opening = 'No' and invoice.docstatus = 1 and
			invoice.company = '{filters.company}' and invoice.posting_date between '{filters.from_date}' and '{filters.to_date}'
		order by
			invoice.posting_date desc
	""",as_dict= True)

	if not filters.show_only_invoice_data:
		# Get Delivery or Receipt where invoice amount is not same or  Delivery or Receipt without invoice
		
		doctype_2 = "Delivery Note" if filters.doctype == "Sales" else "Purchase Receipt"
		child_doctype_2 = doctype_2 + " Item"
		if doctype_2 == "Delivery Note":
			pi_or_si_item = "Sales Invoice Item"
			pi_or_si = "Sales Invoice"
			delivery_receipt_name = "Delivery Note"
			child_si_pi = "dn_detail"
		else:
			pi_or_si_item = "Purchase Invoice Item"
			pi_or_si = "Purchase Invoice"
			delivery_receipt_name = "Purchase Receipt"
			child_si_pi = "pr_detail"

		data += frappe.db.sql(f"""
			select
				dn_pr.name, dn_pr_item.item_code, dn_pr_item.net_amount as receipt_net_amount,
				IFNULL(si_pi.name, null) as invoice_name,
				IF(si_pi.posting_date between '{filters.from_date}' and '{filters.to_date}', IFNULL(pii_sii.net_amount,0), 0) as invoice_amount
			from 
				`tab{doctype_2}` as dn_pr
				JOIN `tab{child_doctype_2}` as dn_pr_item on dn_pr_item.parent = dn_pr.name
				LEFT JOIN `tab{pi_or_si_item}` as pii_sii on pii_sii.{child_si_pi} = dn_pr_item.name and pii_sii.{scrub(delivery_receipt_name)} = dn_pr_item.parent
				LEFT JOIN `tab{pi_or_si}` as si_pi on si_pi.name = pii_sii.parent
			where
				(pii_sii.{scrub(delivery_receipt_name)} is null or pii_sii.{scrub(delivery_receipt_name)} = '' or
				(pii_sii.{scrub(delivery_receipt_name)} is not null and round(dn_pr_item.net_amount) != round(pii_sii.net_amount) and si_pi.docstatus = 1)) and
				dn_pr.docstatus = 1 and
				dn_pr.company = '{filters.company}' and dn_pr.posting_date between '{filters.from_date}' and '{filters.to_date}'
			order by
				dn_pr.posting_date desc
		""",as_dict= True)

	return data

def get_columns(filters):
	columns = [
		{
			"label": _("Invoice"),
			"fieldname": "invoice_name",
			"fieldtype": "Link",
			"options": "Sales Invoice" if filters.doctype == "Sales" else "Purchase Invoice",
			"width": 200
		},
		{
			"label": "Delivery Note" if filters.doctype == "Sales" else "Purchase Receipt",
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Delivery Note" if filters.doctype == "Sales" else "Purchase Receipt",
			"width": 200
		},
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 200
		},
		{
			"label": _("Invoice Amount"),
			"fieldname": "invoice_amount",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": "Delivery Amount" if filters.doctype == "Sales" else "Receipt Amount",
			"fieldname": "receipt_net_amount",
			"fieldtype": "Currency",
			"width": 200
		},
	]
	return columns