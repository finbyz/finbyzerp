from __future__ import unicode_literals
import frappe

def execute():
    update_system_settings()

def update_system_settings():
    doc = frappe.get_doc("System Settings")
    doc.app_name = "FinbyzERP"
    doc.time_format = "HH:mm:ss"
    # doc.db_set("app_name","Finbyz ERP")
    # doc.db_set("time_format","HH:mm:ss")
    doc.save(ignore_permissions=True)
    doc.save(ignore_permissions=True)
    frappe.db.commit()