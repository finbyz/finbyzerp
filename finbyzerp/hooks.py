# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from erpnext.accounts import general_ledger
from erpnext.accounts.report.general_ledger import general_ledger
from erpnext.accounts.report.item_wise_sales_register import item_wise_sales_register
from erpnext.accounts.report.purchase_invoice_trends import purchase_invoice_trends
from erpnext.accounts.report.sales_invoice_trends import sales_invoice_trends
from erpnext.accounts.report.trial_balance_for_party import trial_balance_for_party
from erpnext.controllers import sales_and_purchase_return
from erpnext.controllers.buying_controller import BuyingController
from erpnext.crm.doctype.email_campaign import email_campaign
from erpnext.selling.report.pending_so_items_for_purchase_request import pending_so_items_for_purchase_request
from erpnext.selling.report.sales_order_analysis import sales_order_analysis
from erpnext.stock.doctype.stock_ledger_entry.stock_ledger_entry import StockLedgerEntry
from erpnext.stock.report.stock_balance import stock_balance
from finbyzerp.finbyzerp.override.doctype.email_campaign import send_email_to_leads_or_contacts
from finbyzerp.finbyzerp.override.functionality.buying_controller import set_qty_as_per_stock_uom
from finbyzerp.finbyzerp.override.functionality.db_query import get_date_range
from finbyzerp.finbyzerp.override.functionality.general_ledger import get_result_as_list
from finbyzerp.finbyzerp.override.functionality.permissions import add_permission, download_backup
from finbyzerp.finbyzerp.override.functionality.print_format import get_pdf
from finbyzerp.finbyzerp.override.functionality.sales_and_purchase_return import validate_returned_items
from finbyzerp.finbyzerp.override.functionality.stock_ledger_entry import check_stock_frozen_date
from finbyzerp.finbyzerp.override.functionality.utils import get_timespan_date_range
from finbyzerp.finbyzerp.override.functionality.workflow_action import process_workflow_actions
from finbyzerp.finbyzerp.override.gst_itemised_purchase_register import execute as gst_itemised_purchase_register_execute
from finbyzerp.finbyzerp.override.gst_itemised_sales_register import execute as gst_itemised_sales_register_execute
from finbyzerp.finbyzerp.override.india_compliance.base import get_url as get_gsp_url
from finbyzerp.finbyzerp.override.india_compliance.e_invoice import einvoice_setup
from finbyzerp.finbyzerp.override.india_compliance.e_waybill import ewaybill_setup
from finbyzerp.finbyzerp.override.india_compliance.public import get_gstin_info
from finbyzerp.finbyzerp.override.india_compliance.transaction_data import update_transaction_tax_details
from finbyzerp.finbyzerp.override.item_wise_sales_register import execute as item_wise_sales_register_execute
from finbyzerp.finbyzerp.override.pending_so_items_for_purchase_request import execute as pending_so_items_for_purchase_request_execute
from finbyzerp.finbyzerp.override.report.general_ledger import execute as general_ledger_execute
from finbyzerp.finbyzerp.override.report.permitted_documents_for_user import execute as permitted_documents_for_user_execute
from finbyzerp.finbyzerp.override.report.purchase_invoice_trends import execute as purchase_invoice_trends_execute
from finbyzerp.finbyzerp.override.report.sales_invoice_trends import execute as sales_invoice_trends_execute
from finbyzerp.finbyzerp.override.report.stock_balance import execute as stock_balance_execute
from finbyzerp.finbyzerp.override.sales_order_analysis import execute as sales_order_analysis_execute
from finbyzerp.finbyzerp.override.trial_balance_for_party import execute as trial_balance_for_party_execute
from frappe import permissions, utils
from frappe.core.report.permitted_documents_for_user import permitted_documents_for_user
from frappe.model import db_query
from frappe.utils import pdf, response
from frappe.workflow.doctype.workflow_action import workflow_action
from india_compliance.gst_india.api_classes.base import BaseAPI
from india_compliance.gst_india.api_classes.e_invoice import EInvoiceAPI
from india_compliance.gst_india.api_classes.e_waybill import EWaybillAPI
from india_compliance.gst_india.api_classes.public import PublicAPI
from india_compliance.gst_india.report.gst_itemised_purchase_register import gst_itemised_purchase_register
from india_compliance.gst_india.report.gst_itemised_sales_register import gst_itemised_sales_register
from india_compliance.gst_india.utils.transaction_data import GSTTransactionData

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
# after_install = "finbyzerp.install.after_install"

app_include_js = "finbyzerp.bundle.js"
app_include_css = "finbyzerp.bundle.css"
# before_install = "finbyzerp.install.before_install"

website_context = {
    "favicon": "/assets/finbyzerp/images/favicon.ico",
    "splash_image": "/assets/finbyzerp/images/FinbyzLogo.svg",
}

doctype_list_js = {
    "Batch": "public/js/doctype_js/batch_list.js",
    "Repost Item Valuation": "public/js/doctype_js/repost_item_valuation_list.js",
}

doctype_js = {
    "Role Profile": "public/js/doctype_js/role_profile.js",
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
    "Lead": "public/js/doctype_js/lead.js",
    "Customer": "public/js/doctype_js/customer.js",
    "Opportunity": "public/js/doctype_js/opportunity.js",
    "Opening Invoice Creation Tool": "public/js/doctype_js/opening_invoice_creation_tool.js",
    "Payment Reconciliation": "public/js/doctype_js/payment_reconciliation.js",
    "BOM": "public/js/doctype_js/bom.js",
    "Quotation": "public/js/doctype_js/quotation.js",
}

doc_events = {
    (
        "Pick List",
        "Sales Invoice",
        "Purchase Invoice",
        "Payment Request",
        "Payment Entry",
        "Journal Entry",
        "Material Request",
        "Purchase Order",
        "Work Order",
        "Production Plan",
        "Stock Entry",
        "Quotation",
        "Sales Order",
        "Delivery Note",
        "Purchase Receipt",
        "Packing Slip",
        "Credit and Debit Note",
        "Asset",
    ): {
        "before_naming": "finbyzerp.finbyzerp.doc_events.naming_series.before_naming",
    },
    ("Quotation", "Sales Order", "Delivery Note", "Sales Invoice"): {
        "on_submit": "finbyzerp.finbyzerp.doc_events.sales_comment.on_submit",
        "before_update_after_submit": "finbyzerp.finbyzerp.doc_events.sales_comment.before_update_after_submit",
        "before_cancel": "finbyzerp.finbyzerp.doc_events.sales_comment.on_cancel",
        "on_trash": "finbyzerp.finbyzerp.doc_events.sales_comment.on_trash",
    },
    ("Journal Entry", "Stock Entry", "Purchase Invoice", "Sales Invoice"): {
        "before_insert": "finbyzerp.finbyzerp.doc_events.naming_series.before_insert",
    },
    ("Customer", "Supplier"): {
        "validate": "finbyzerp.finbyzerp.doc_events.customer_supplier.validate",
        "before_rename": "finbyzerp.finbyzerp.doc_events.customer_supplier.before_rename",
    },
    ("Purchase Order", "Sales Order"): {
        "before_cancel": "finbyzerp.finbyzerp.doc_events.sales_purchase_order.before_cancel",
    },
    ("Purchase Order", "Purchase Receipt", "Purchase Invoice"): {
        "validate": "finbyzerp.finbyzerp.doc_events.conversion_factor.validate",
    },
    "Fiscal Year": {"before_save": "finbyzerp.finbyzerp.doc_events.fiscal_year.before_save"},
    "Sales Invoice": {
        "before_save": "finbyzerp.finbyzerp.doc_events.sales_invoice.before_save",
        "validate": [
            "finbyzerp.finbyzerp.doc_events.sales_invoice.validate",
            "finbyzerp.finbyzerp.doc_events.sales_purchase_invoice.validate",
        ],
        "on_trash": "finbyzerp.finbyzerp.doc_events.sales_invoice.on_trash",
        "on_submit": "finbyzerp.finbyzerp.doc_events.sales_invoice.on_submit",
    },
    "Purchase Invoice": {
        "validate": "finbyzerp.finbyzerp.doc_events.sales_purchase_invoice.validate",
    },
    "Stock Settings": {
        "validate": "finbyzerp.finbyzerp.doc_events.stock_settings.validate",
    },
    "User": {"validate": "finbyzerp.finbyzerp.doc_events.user.validate"},
    "Purchase Receipt": {"on_submit": "finbyzerp.finbyzerp.doc_events.purchase_receipt.on_submit"},
    "Delivery Note": {"validate": "finbyzerp.finbyzerp.doc_events.delivery_note.validate"},
    "Stock Entry": {
        "validate": "finbyzerp.finbyzerp.doc_events.stock_entry.validate",
        "after_insert": "finbyzerp.finbyzerp.doc_events.stock_entry.agter_insert",
        "on_submit": "finbyzerp.finbyzerp.doc_events.stock_entry.on_submit",
    },
    "Item": {
        "validate": "finbyzerp.finbyzerp.doc_events.item.validate",
        "before_naming": "finbyzerp.finbyzerp.doc_events.item.before_validate",
        "before_rename": "finbyzerp.finbyzerp.doc_events.item.before_rename",
    },
}

override_doctype_class = {
    "Customize Form": "finbyzerp.finbyzerp.override.doctype.customize_form.CustomCustomizeForm",
    "Custom Field": "finbyzerp.finbyzerp.override.doctype.custom_field.CustomFieldOverride",
    "Report": "finbyzerp.finbyzerp.override.doctype.report.CustomReport",
    "Document Naming Settings": "finbyzerp.finbyzerp.override.doctype.document_naming_settings.CustomDocumentNamingSettings",
    "Opening Invoice Creation Tool": "finbyzerp.finbyzerp.override.doctype.opening_invoice_creation_tool.CustomOpeningInvoiceCreationTool",
}

override_doctype_dashboards = {
    "Lead": "finbyzerp.finbyzerp.dashboard.lead.get_data",
    "Customer": "finbyzerp.finbyzerp.dashboard.customer.get_data",
    "Opportunity": "finbyzerp.finbyzerp.dashboard.opportunity.get_data",
}

override_whitelisted_methods = {
    "frappe.core.page.permission_manager.permission_manager.get_roles_and_doctypes": "finbyzerp.finbyzerp.override.functionality.permissions.get_roles_and_doctypes",
    "frappe.core.page.permission_manager.permission_manager.get_permissions": "finbyzerp.finbyzerp.override.functionality.permissions.get_permissions",
    "frappe.core.page.permission_manager.permission_manager.add": "finbyzerp.finbyzerp.override.functionality.permissions.add",
    "frappe.core.page.permission_manager.permission_manager.update": "finbyzerp.finbyzerp.override.functionality.permissions.update",
    "frappe.core.page.permission_manager.permission_manager.remove": "finbyzerp.finbyzerp.override.functionality.permissions.remove",
    "frappe.core.page.permission_manager.permission_manager.reset": "finbyzerp.finbyzerp.override.functionality.permissions.reset",
    "frappe.core.page.permission_manager.permission_manager.get_users_with_role": "finbyzerp.finbyzerp.override.functionality.permissions.get_users_with_role",
    "frappe.core.page.permission_manager.permission_manager.get_standard_permissions": "finbyzerp.finbyzerp.override.functionality.permissions.get_standard_permissions",
    "erpnext.setup.doctype.company.delete_company_transactions.delete_company_transactions": "finbyzerp.finbyzerp.override.delete_company_transactions.delete_company_transactions",
    "india_compliance.gst_india.utils.e_invoice.generate_e_invoice": "finbyzerp.e_invoice_override_14.custom_generate_e_invoice",
}

scheduler_events = {
    "daily": [
        "finbyzerp.scheduler.daily_entry_summary_mail",
        "finbyzerp.scheduler.daily_transaction_summary_mail",
    ]
}


# Functionality Overrides
permissions.add_permission = add_permission
response.download_backup = download_backup
pdf.get_pdf = get_pdf
utils.get_timespan_date_range = get_timespan_date_range
db_query.get_date_range = get_date_range
workflow_action.process_workflow_actions = process_workflow_actions
sales_and_purchase_return.validate_returned_items = validate_returned_items
BuyingController.set_qty_as_per_stock_uom = set_qty_as_per_stock_uom
general_ledger.get_result_as_list = get_result_as_list
StockLedgerEntry.check_stock_frozen_date = check_stock_frozen_date
email_campaign.send_email_to_leads_or_contacts = send_email_to_leads_or_contacts

# India Compliance Overrides
EInvoiceAPI.setup = einvoice_setup
EWaybillAPI.setup = ewaybill_setup
BaseAPI.get_url = get_gsp_url
PublicAPI.get_gstin_info = get_gstin_info
GSTTransactionData.update_transaction_tax_details = update_transaction_tax_details
sales_order_analysis.execute = sales_order_analysis_execute
pending_so_items_for_purchase_request.execute = pending_so_items_for_purchase_request_execute

# Report
permitted_documents_for_user.execute = permitted_documents_for_user_execute
stock_balance.execute = stock_balance_execute
sales_invoice_trends.execute = sales_invoice_trends_execute
purchase_invoice_trends.execute = purchase_invoice_trends_execute
permitted_documents_for_user.execute = permitted_documents_for_user_execute
item_wise_sales_register.execute = item_wise_sales_register_execute
trial_balance_for_party.execute = trial_balance_for_party_execute
general_ledger.execute = general_ledger_execute

# India Compliance Report
gst_itemised_sales_register.execute = gst_itemised_sales_register_execute
gst_itemised_purchase_register.execute = gst_itemised_purchase_register_execute
