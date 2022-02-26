from __future__ import unicode_literals
import frappe

def execute():
    create_unallocate_payment_field()

def create_unallocate_payment_field():
    doc = frappe.new_doc("Custom Field")
    doc.dt = "Payment Entry Reference"
    doc.label = "Unallocate Payment"
    doc.fieldname = "unallocate_payment"
    doc.insert_after = "reference_doctype"
    doc.fieldtype = "Button"
    doc.save(ignore_permissions=True)