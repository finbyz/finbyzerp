from __future__ import unicode_literals
import frappe

def execute():
	if frappe.db.sql("SHOW COLUMNS FROM `tabSales Invoice` LIKE 'signed_qr_code'"):
		frappe.db.sql("ALTER TABLE `tabSales Invoice` DROP COLUMN `signed_qr_code`")

	if frappe.db.sql("SHOW COLUMNS FROM `tabSales Invoice` LIKE 'qrcode_image'"):
		frappe.db.sql("ALTER TABLE `tabSales Invoice` DROP COLUMN `qrcode_image`")
