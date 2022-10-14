from __future__ import unicode_literals
import frappe

def execute():
    create_rate_field()

def create_rate_field():
    doc = frappe.new_doc("Custom Field")
    doc.dt = "Account"
    doc.label = "Interest Rate"
    doc.fieldname = "interest_rate"
    doc.insert_after = "tax_rate"
    doc.fieldtype = "Float"
    doc.save(ignore_permissions=True)

    doc = frappe.new_doc("Custom Field")
    doc.dt = "Company"
    doc.label = "Default Interest Rate"
    doc.fieldname = "default_interest_rate"
    doc.insert_after = "_default_quality_inspection"
    doc.fieldtype = "Float"
    doc.save(ignore_permissions=True)