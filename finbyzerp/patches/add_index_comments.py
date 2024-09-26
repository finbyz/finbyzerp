import frappe

def execute():
    frappe.db.add_index("Comment", ["reference_doctype", "creation"])