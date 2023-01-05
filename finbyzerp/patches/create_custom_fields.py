from __future__ import unicode_literals
import frappe

def execute():
    create_unallocate_payment_field()
    create_qty_as_per_bom_for_se()

def create_unallocate_payment_field():
    doc = frappe.new_doc("Custom Field")
    doc.dt = "Payment Entry Reference"
    doc.label = "Unallocate Payment"
    doc.fieldname = "unallocate_payment"
    doc.insert_after = "reference_doctype"
    doc.fieldtype = "Button"
    doc.save(ignore_permissions=True)

def create_qty_as_per_bom_for_se():
    if not frappe.db.exists("Custom Field", {'label': 'Qty as Per BOM', 'fieldname': 'qty_as_per_bom'}):
        doc = frappe.new_doc("Custom Field")
        doc.dt = "Stock Entry"
        doc.label = "Qty as Per BOM"
        doc.fieldname = "qty_as_per_bom"
        doc.insert_after = "apply_putaway_rule"
        doc.depends_on = 'eval: doc.stock_entry_type == "Manufacture" && doc.docstatus == 0 && doc.bom_no && doc.work_order;'
        doc.fieldtype = "Button"
        doc.save(ignore_permissions=True)