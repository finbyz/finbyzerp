from __future__ import unicode_literals
import frappe

def execute():
	if row := frappe.db.get_value("Custom Field", filters={"dt": "Sales Invoice", "fieldname": "signed_qr_code"}, fieldname="name"):
		frappe.delete_doc("Custom Field", row, delete_permanently=True)

	if row := frappe.db.get_value("Custom Field", filters={"dt": "Sales Invoice", "fieldname": "qrcode_image"}, fieldname="name"):
		frappe.delete_doc("Custom Field", row, delete_permanently=True)
