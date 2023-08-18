from __future__ import unicode_literals
import frappe

def execute():
    create_comment()

def create_comment():
    if not frappe.db.exists("Custom Field", "System Settings-create_comments"):
        doc = frappe.new_doc("Custom Field")
        doc.dt = "System Settings"
        doc.label = "Create Comments"
        doc.fieldname = "create_comments"
        doc.insert_after = "disable_invoice_length_check"
        doc.fieldtype = "Check"
        doc.save(ignore_permissions = True)