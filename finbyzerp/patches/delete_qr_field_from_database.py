from __future__ import unicode_literals
import frappe

def execute():
	if row := frappe.db.get_value("Custom Field", filters={"dt": "Sales Invoice", "fieldname": "signed_qr_code"}, fieldname="name"):
		frappe.delete_doc("Custom Field", row, delete_permanently=True)

	if row := frappe.db.get_value("Custom Field", filters={"dt": "Sales Invoice", "fieldname": "qrcode_image"}, fieldname="name"):
		frappe.delete_doc("Custom Field", row, delete_permanently=True)

	data = frappe.db.get_all("File", filters={"attached_to_doctype": "Sales Invoice", "attached_to_field": "qrcode_image"})
	for i in data:
		frappe.delete_doc("File", i.name)
