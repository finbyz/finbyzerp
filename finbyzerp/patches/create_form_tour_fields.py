from __future__ import unicode_literals
import frappe

def execute():
    create_form_tour_fields()

def create_form_tour_fields():

    doc_ = frappe.new_doc("Custom Field")
    doc_.dt = "Form Tour"
    doc_.label = "Module"
    doc_.fieldname = "module"
    doc_.insert_after = "reference_doctype"
    doc_.fieldtype = "Link"
    doc_.options="Module Def"
    doc_.fetch_from= "reference_doctype.module"
    doc_.hidden=0
    doc_.read_only=1
    doc_.save(ignore_permissions=True)

    doc = frappe.new_doc("Custom Field")
    doc.dt = "Form Tour"
    doc.label = "Is Standard"
    doc.fieldname = "is_standard"
    doc.insert_after = "module"
    doc.fieldtype = "Check"
    doc.default=0
    doc.save(ignore_permissions=True)

    