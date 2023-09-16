from __future__ import unicode_literals
import frappe

def execute():
    create_disable_invoice_name_length_check_field()
    create_comment()
    
def create_disable_invoice_name_length_check_field():
    doc = frappe.new_doc("Custom Field")
    doc.dt = "System Settings"
    doc.label = "Disable Invoice Length Check"
    doc.fieldname = "disable_invoice_length_check"
    doc.insert_after = "enable_onboarding"
    doc.fieldtype = "Check"
    doc.save(ignore_permissions=True)

def create_comment():
    doc = frappe.new_doc("Custom Field")
    doc.dt = "System Settings"
    doc.label = "Disable Timeline of Document Creation"
    doc.fieldname = "create_comments"
    doc.insert_after = "disable_invoice_length_check"
    doc.fieldtype = "Check"
    doc.save(ignore_permissions = True)