from __future__ import unicode_literals
import frappe

def execute():
    doc = frappe.new_doc("Custom DocPerm")
    doc.parent = "System Settings"
    doc.role = "System Manager"
    doc.permlevel = 3
    doc.read = 1
    doc.write = 1
    doc.submit = 1
    doc.cancel = 1
    doc.create = 1
    doc.delete = 1
    doc.export = 1
    doc.save(ignore_permissions=True)