# -*- coding: utf-8 -*-
# Imports

from __future__ import unicode_literals
from erpnext.selling.report.pending_so_items_for_purchase_request import (
    pending_so_items_for_purchase_request,
)
from erpnext.selling.report.sales_order_analysis import sales_order_analysis
from finbyzerp.finbyzerp.override.pending_so_items_for_purchase_request import (
    execute as pending_so_items_for_purchase_request_execute,
)
from finbyzerp.finbyzerp.override.sales_order_analysis import (
    execute as sales_order_analysis_execute,
)

from . import __version__ as app_version

app_name = "finbyzerp"
app_title = "FinByz ERP"
app_publisher = "Finbyz Tech Pvt Ltd"
app_description = "FinByz ERP"
app_icon = "octicon octicon-diff-ignored"
app_color = "blue"
app_email = "info@finbyz.com"
app_license = "GPL 3.0"
app_version = app_version
app_logo_url = "/assets/finbyzerp/images/FinbyzLogo.svg"

app_include_js = "finbyzerp.bundle.js"
app_include_css = "finbyzerp.bundle.css"

website_context = {
    "favicon": "/assets/finbyzerp/images/favicon.ico",
    "splash_image": "/assets/finbyzerp/images/FinbyzLogo.svg",
}

# doctype_list_js = {
#     "Batch": "public/js/doctype_js/batch_list.js",
# }
fixtures = [
    {
        "dt": "Custom Field",
        "filters": {"module": ["in", ["Finbyzerp"]]},
    }
]
# Doctype Js
doctype_js = {
    "Sales Order": "public/js/doctype_js/sales_order.js",
    "Delivery Note": "public/js/doctype_js/delivery_note.js",
    "Sales Invoice": "public/js/doctype_js/sales_invoice.js",
    "Purchase Order": "public/js/doctype_js/purchase_order.js",
    "Purchase Receipt": "public/js/doctype_js/purchase_receipt.js",
    "Purchase Invoice": "public/js/doctype_js/purchase_invoice.js",
    "Payment Entry": "public/js/doctype_js/payment_entry.js",
    "Stock Entry": "public/js/doctype_js/stock_entry.js",
    "Account": "public/js/doctype_js/account.js",
    "GST Settings": "public/js/doctype_js/gst_settings.js",
    "Opportunity": "public/js/doctype_js/opportunity.js",
    "Opening Invoice Creation Tool": "public/js/doctype_js/opening_invoice_creation_tool.js",
    "BOM": "public/js/doctype_js/bom.js",
    "Quotation": "public/js/doctype_js/quotation.js",
}

# Doc Events
doc_events = {
    "*": {
        "before_naming": "finbyzerp.finbyzerp.doc_events.naming_series.before_naming",
    },
    ("Quotation", "Sales Order", "Delivery Note", "Sales Invoice"): {
        "on_submit": "finbyzerp.finbyzerp.doc_events.sales_comment.on_submit",
        "before_update_after_submit": "finbyzerp.finbyzerp.doc_events.sales_comment.before_update_after_submit",
        "before_cancel": "finbyzerp.finbyzerp.doc_events.sales_comment.on_cancel",
        "on_trash": "finbyzerp.finbyzerp.doc_events.sales_comment.on_trash",
    },
    "Sales Order":{
        "validate" : "finbyzerp.finbyzerp.doc_events.sales_order.validate",
        "on_update_after_submit": "finbyzerp.finbyzerp.doc_events.sales_order.on_update_after_submit",
    },
    ("Purchase Order", "Purchase Receipt", "Purchase Invoice"): {
        "validate": "finbyzerp.finbyzerp.doc_events.conversion_factor.validate",
    },
    "Purchase Order": {
        "validate":  "finbyzerp.finbyzerp.doc_events.purchase_order.validate",
        "on_update_after_submit": "finbyzerp.finbyzerp.doc_events.purchase_order.on_update_after_submit",
    },
    "Fiscal Year": {
        "before_save": "finbyzerp.finbyzerp.doc_events.fiscal_year.before_save"
    },
    "Sales Invoice": {
        "before_save": "finbyzerp.finbyzerp.doc_events.sales_invoice.before_save",
        "validate": [
            "finbyzerp.finbyzerp.doc_events.sales_invoice.validate",
            "finbyzerp.finbyzerp.doc_events.purchase_invoice.validate",
        ],
        "on_trash": "finbyzerp.finbyzerp.doc_events.sales_invoice.on_trash",
        "on_submit": "finbyzerp.finbyzerp.doc_events.sales_invoice.on_submit",
        "on_update_after_submit": "finbyzerp.finbyzerp.doc_events.sales_invoice.on_update_after_submit",
    },
    "Purchase Invoice": {
        "validate": "finbyzerp.finbyzerp.doc_events.sales_purchase_invoice.validate",    
    },
    "Payment Entry": {
        "validate": "finbyzerp.finbyzerp.doc_events.payment_entry.validate",
        "on_update_after_submit": "finbyzerp.finbyzerp.doc_events.payment_entry.on_update_after_submit",
    },
    "Stock Settings": {
        "validate": "finbyzerp.finbyzerp.doc_events.stock_settings.validate",
    },
    "Purchase Receipt": {
        "on_submit": "finbyzerp.finbyzerp.doc_events.purchase_receipt.on_submit"
    },
    # "Stock Entry": {
    #     "validate": "finbyzerp.finbyzerp.doc_events.stock_entry.validate",
    #     "after_insert": "finbyzerp.finbyzerp.doc_events.stock_entry.after_insert",
    #     "on_submit": "finbyzerp.finbyzerp.doc_events.stock_entry.on_submit",
    # },
    "Item": {
        "validate": "finbyzerp.finbyzerp.doc_events.item.validate",
        "before_naming": "finbyzerp.finbyzerp.doc_events.item.before_validate",
        "before_rename": "finbyzerp.finbyzerp.doc_events.item.before_rename",
    },
}

# Override Doctype Class
override_doctype_class = {
    "Customize Form": "finbyzerp.finbyzerp.override.doctype.customize_form.CustomizeForm",
    "Custom Field": "finbyzerp.finbyzerp.override.doctype.custom_field.CustomFieldOverride",
    "Document Naming Settings": "finbyzerp.finbyzerp.override.doctype.document_naming_settings.DocumentNamingSettings",
    "Opening Invoice Creation Tool": "finbyzerp.finbyzerp.override.doctype.opening_invoice_creation_tool.OpeningInvoiceCreationTool",
    "Address": "finbyzerp.finbyzerp.override.doctype.address.Address",
}

# Override Doctype Dashboards
override_doctype_dashboards = {
    "Lead": "finbyzerp.finbyzerp.override.override_doctype_dashboards.lead.get_data",
    "Customer": "finbyzerp.finbyzerp.override.override_doctype_dashboards.customer.get_data",
    "Opportunity": "finbyzerp.finbyzerp.override.override_doctype_dashboards.opportunity.get_data",
}

override_whitelisted_methods = {
    "frappe.modules.utils.export_customizations":"finbyzerp.finbyzerp.override.doctype.customize_form.export_customizations", 
}

# Scheduler Events
scheduler_events = {
    # "daily": [
    #     "finbyzerp.scheduler.daily_entry_summary_mail",
    #     "finbyzerp.scheduler.daily_transaction_summary_mail",
    # ],
    "cron":{
		"0 4 * * SUN": [
			"finbyzerp.api.sales_invoice_payment_remainder",
		]
	},
}




# Report
sales_order_analysis.execute = sales_order_analysis_execute
pending_so_items_for_purchase_request.execute = pending_so_items_for_purchase_request_execute

