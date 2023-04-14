from __future__ import unicode_literals
import frappe

def execute():
    create_custom_field_for_einvoice()

def create_custom_field_for_einvoice():
    if not frappe.db.exists("Custom Field", "GST Settings-client_secret"):
        doc = frappe.new_doc("Custom Field")
        doc.dt = "GST Settings"
        doc.label = "Client Secret"
        doc.fieldname = "client_secret"
        doc.insert_after = "column_break_4"
        doc.fieldtype = "Password"
        doc.depends_on = "eval: doc.enable_api"
        doc.save(ignore_permissions=True)

    if not frappe.db.exists("Custom Field", "GST Settings-client_id"):
        doc = frappe.new_doc("Custom Field")
        doc.dt = "GST Settings"
        doc.label = "Client Id"
        doc.fieldname = "client_id"
        doc.insert_after = "generat_tab"
        doc.fieldtype = "Data"
        doc.depends_on = "eval: doc.enable_api"
        doc.save(ignore_permissions=True)
   
    if not frappe.db.exists("Custom Field", "GST Settings-token_expiry"):
        doc = frappe.new_doc("Custom Field")
        doc.dt = "GST Settings"
        doc.label = "Token Expiry"
        doc.fieldname = "token_expiry"
        doc.insert_after = "auth_token"
        doc.fieldtype = "Datetime"
        doc.read_only == 1 
        doc.save(ignore_permissions=True)

    if not frappe.db.exists("Custom Field", "GST Settings-auth_token"):
        doc = frappe.new_doc("Custom Field")
        doc.dt = "GST Settings"
        doc.label = "Auth Token"
        doc.fieldname = "auth_token"
        doc.insert_after = "api_secret"
        doc.fieldtype = "Data"
        doc.read_only == 1 
        doc.save(ignore_permissions=True)

    if not frappe.db.exists("Custom Field", "Sales Invoice-qrcode_image"):
        doc = frappe.new_doc("Custom Field")
        doc.dt = "Sales Invoice"
        doc.label = "QRCode Image"
        doc.fieldname = "qrcode_image"
        doc.insert_after = "Eway bill json Required"
        doc.fieldtype = "Code"
        doc.options = "JSON"
        doc.read_only == 1
        doc.hidden==1
        doc.no_copy == 1
        doc.allow_on_submit == 1
    
        doc.save(ignore_permissions=True)