# -*- coding: utf-8 -*-
from __future__ import unicode_literals
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


after_install = "finbyzerp.install.after_install"

# from erpnext.regional.doctype.gstr_3b_report.gstr_3b_report import GSTR3BReport
# from finbyzerp.finbyzerp.override.gstr_3b_report import prepare_data, get_itc_details, get_inter_state_supplies, get_tax_amounts
# GSTR3BReport.prepare_data = prepare_data
# GSTR3BReport.get_itc_details = get_itc_details
# GSTR3BReport.get_inter_state_supplies = get_inter_state_supplies
# GSTR3BReport.get_tax_amounts = get_tax_amounts

#depreciated in v13
# from erpnext.setup.doctype.naming_series.naming_series import NamingSeries
# from finbyzerp.finbyzerp.override.naming_series import get_transactions
# NamingSeries.get_transactions = get_transactions

from frappe.core.doctype.document_naming_settings.document_naming_settings import DocumentNamingSettings
from finbyzerp.finbyzerp.override.naming_series import _get_prefixes as get_prefixes
DocumentNamingSettings._get_prefixes = get_prefixes

from erpnext.accounts.doctype.opening_invoice_creation_tool.opening_invoice_creation_tool import OpeningInvoiceCreationTool
from finbyzerp.finbyzerp.doc_events.opening_invoice_creation_tool import get_invoice_dict, make_invoices

OpeningInvoiceCreationTool.get_invoice_dict = get_invoice_dict
OpeningInvoiceCreationTool.make_invoices = make_invoices


from frappe.core.doctype.report.report import Report
from finbyzerp.api import report_validate
Report.validate = report_validate

from frappe.utils import dashboard
from finbyzerp.finbyzerp.override.dashboard_override import make_records
dashboard.make_records = make_records

# # e_invoice overrides
import erpnext
import india_compliance
from finbyzerp.e_invoice_override_14 import get_item_list, validate_einvoice_fields, validate_document_name, make_einvoice
from india_compliance.gst_india.utils.transaction_data import GSTTransactionData
GSTTransactionData.get_item_list = get_item_list
# erpnext.regional.india.e_invoice.utils.validate_einvoice_fields = validate_einvoice_fields
# erpnext.regional.india.e_invoice.utils.make_einvoice = make_einvoice

# # from finbyzerp.e_invoice_override import validate_einvoice_fields,get_transaction_details,get_item_list,make_einvoice,get_invoice_value_details,update_invoice_taxes
# # erpnext.regional.india.e_invoice.utils.get_transaction_details = get_transaction_details
# # erpnext.regional.india.e_invoice.utils.get_invoice_value_details=get_invoice_value_details
# # erpnext.regional.india.e_invoice.utils.update_invoice_taxes = update_invoice_taxes
# #erpnext.regional.india.e_invoice.utils.update_item_taxes = update_item_taxes
# #erpnext.regional.india.e_invoice.utils.get_party_details = get_party_details


# from erpnext.regional.india import utils
# utils.validate_document_name = validate_document_name

#from erpnext.regional.india.e_invoice.utils import GSPConnector
#GSPConnector.set_einvoice_data = set_einvoice_data

from frappe.core.report.permitted_documents_for_user import permitted_documents_for_user
from finbyzerp.api import execute
permitted_documents_for_user.execute = execute
# import erpnext
# from finbyzerp.e_invoice_override import get_item_list,validate_einvoice_fields
# erpnext.regional.india.e_invoice.utils.validate_einvoice_fields = validate_einvoice_fields
# erpnext.regional.india.e_invoice.utils.get_item_list = get_item_list

#Override for customdocperm permition
from frappe import permissions
from finbyzerp.api import add_permission
permissions.add_permission = add_permission


# email Campaign override
from finbyzerp.finbyzerp.doc_events.email_campaign import send_email_to_leads_or_contacts
from erpnext.crm.doctype.email_campaign import email_campaign
email_campaign.send_email_to_leads_or_contacts = send_email_to_leads_or_contacts

# override for workspace migration issue
# from frappe.model import sync 
# from finbyzerp.api import get_doc_files
# sync.get_doc_files = get_doc_files


app_include_css = ["finbyzerp.bundle.css"]
app_include_js = [
	"finbyzerp.bundle.js"
]

doctype_list_js = {
	"Batch" : "public/js/doctype_js/batch_list.js",
	"Fiscal Year" : "public/js/doctype_js/fiscal_year.js",
	"Repost Item Valuation":"public/js/doctype_js/repost_item_valuation_list.js"
}

before_install = "finbyzerp.install.before_install"
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
	"Account":"public/js/doctype_js/account.js",
	"GST Settings":"public/js/doctype_js/gst_settings.js",
	"Lead":"public/js/doctype_js/lead.js",
	"Customer":"public/js/doctype_js/customer.js",
	"Opportunity":"public/js/doctype_js/opportunity.js",
	"Opening Invoice Creation Tool":"public/js/doctype_js/opening_invoice_creation_tool.js",
	"Payment Reconciliation":"public/js/doctype_js/payment_reconciliation.js",
	"BOM":"public/js/doctype_js/bom.js",
	"Form Tour": "public/js/doctype_js/form_tour.js",
    "Quotation": "public/js/doctype_js/quotation.js",
	"Quick Stock Balance": "public/js/doctype_js/quick_stock_balance.js"
}
website_context = {
	"favicon": 	"/assets/finbyzerp/images/favicon.ico",
	"splash_image": "/assets/finbyzerp/images/FinbyzLogo.svg"
}

override_doctype_class = {
	"Opportunity": "finbyzerp.finbyzerp.override.opportunity.CustomOpportunity",
    "Custom Field": "finbyzerp.finbyzerp.override.custom_field.CustomFieldOverride",
    "Customize Form": "finbyzerp.finbyzerp.override.customize_form.CustomizeForm",
    "Quality Inspection": "finbyzerp.finbyzerp.override.quality_inspection.QualityInspection",
    "Sales Invoice": "finbyzerp.finbyzerp.override.sales_invoice.SalesInvoice",
    "Purchase Invoice": "finbyzerp.finbyzerp.override.purchase_invoice.PurchaseInvoice",
    "Authorization Rule": "finbyzerp.finbyzerp.override.authorization_rule.AuthorizationRule",
}

override_whitelisted_methods = {
	"frappe.core.page.permission_manager.permission_manager.get_roles_and_doctypes": "finbyzerp.permission.get_roles_and_doctypes",
	"frappe.core.page.permission_manager.permission_manager.get_permissions": "finbyzerp.permission.get_permissions",
	"frappe.core.page.permission_manager.permission_manager.add": "finbyzerp.permission.add",
	"frappe.core.page.permission_manager.permission_manager.update": "finbyzerp.permission.update",
	"frappe.core.page.permission_manager.permission_manager.remove": "finbyzerp.permission.remove",
	"frappe.core.page.permission_manager.permission_manager.reset": "finbyzerp.permission.reset",
	"frappe.core.page.permission_manager.permission_manager.get_users_with_role": "finbyzerp.permission.get_users_with_role",
	"frappe.core.page.permission_manager.permission_manager.get_standard_permissions": "finbyzerp.permission.get_standard_permissions",
	"erpnext.setup.doctype.company.delete_company_transactions.delete_company_transactions": "finbyzerp.finbyzerp.override.delete_company_transactions.delete_company_transactions",
	"frappe.desk.moduleview.get_desktop_settings": "finbyzerp.api.get_desktop_settings",
	"frappe.desk.moduleview.get_options_for_global_modules": "finbyzerp.api.get_options_for_global_modules",
	# "india_compliance.gst_india.utils.e_invoice.generate_e_invoice" : "finbyzerp.e_invoice_override_14.custom_generate_e_invoice",
	# "erpnext.regional.india.e_invoice.utils.cancel_eway_bill": "finbyzerp.e_invoice_override.cancel_eway_bill", # cancel eway bill override for enable cancel_eway_bill api
	#"frappe.utils.print_format.download_pdf": "finbyzerp.print_format.download_pdf",
	"erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice" : "finbyzerp.api.make_purchase_invoice",
    "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt" : "finbyzerp.api.make_purchase_receipt",
    "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice":"finbyzerp.api.make_sales_invoice",
    "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note":"finbyzerp.api.make_delivery_note",
    "frappe.modules.utils.export_customizations":"finbyzerp.finbyzerp.override.customize_form.export_customizations", 
}

# override for supplier query
from erpnext.controllers import queries
from finbyzerp.queries import supplier_query as custom_supplier_query
queries.supplier_query = custom_supplier_query

# override for download backup
from frappe.utils import response
from finbyzerp.permission import download_backup
response.download_backup = download_backup

override_doctype_dashboards = {
	"Lead": "finbyzerp.finbyzerp.dashboard.lead.get_data",
	"Customer":"finbyzerp.finbyzerp.dashboard.customer.get_data",
	"Opportunity":"finbyzerp.finbyzerp.dashboard.opportunity.get_data"
}

doc_events = {
	"Customer": {
		"validate":"finbyzerp.api.customer_validate",
		"before_rename": "finbyzerp.finbyzerp.doc_events.customer.before_rename",
	},
	"Supplier": {
		"validate":"finbyzerp.api.supplier_validate",
		"before_rename": "finbyzerp.finbyzerp.doc_events.supplier.before_rename"
	},
	"Item": {
		"validate":"finbyzerp.finbyzerp.doc_events.item.validate",
		"before_naming":"finbyzerp.finbyzerp.doc_events.item.before_validate",
		"before_rename": "finbyzerp.finbyzerp.doc_events.item.before_rename"
	},
	"User": {
		"validate":"finbyzerp.api.validate_user"
	},
	"Sales Invoice": {
		"before_insert": "finbyzerp.api.before_insert",
		"before_save":"finbyzerp.finbyzerp.doc_events.sales_invoice.before_save",
		"validate":[
			"finbyzerp.finbyzerp.doc_events.sales_invoice.validate",
			"finbyzerp.api.si_validate"
		],
		"on_trash": "finbyzerp.finbyzerp.doc_events.sales_invoice.on_trash",
		# "on_submit": "finbyzerp.api.sales_invoice_on_submit",
        "on_update_after_submit": "finbyzerp.finbyzerp.doc_events.sales_invoice.on_update_after_submit",
	},
     ("Purchase Order", "Purchase Receipt", "Purchase Invoice"): {
		"validate":"finbyzerp.finbyzerp.override.override_conversion_factor.validate_conversion",
	},
	"Purchase Invoice": {
		"before_insert": "finbyzerp.api.before_insert",
		"validate": "finbyzerp.api.pi_validate",
	},
	"Purchase Receipt": {
		"on_submit": "finbyzerp.finbyzerp.doc_events.purchase_receipt.set_batch_in_qc"
	},
	"Stock Entry": {
		"validate": [
			"finbyzerp.api.stock_entry_validate",
			# "finbyzerp.finbyzerp.doc_events.stock_entry.validate",
            # "finbyzerp.finbyzerp.doc_events.stock_entry.create_quality_inspection_entry"
		],
        "after_insert": [
			"finbyzerp.finbyzerp.doc_events.stock_entry.after_insert",
		],
		"on_submit": [
			"finbyzerp.api.stock_entry_on_submit",
            "finbyzerp.finbyzerp.doc_events.stock_entry.on_submit"
		],
		"before_insert": "finbyzerp.api.before_insert",
	},
	"Journal Entry":{
		"before_insert": "finbyzerp.api.before_insert",
	},
	# "Payment Entry":{
	# 	# "validate":"finbyzerp.finbyzerp.doc_events.payment_entry.validate"
	# },
	"Delivery Note":{
		"validate":"finbyzerp.finbyzerp.doc_events.delivery_note.validate"
	},
	("Purchase Order","Sales Order"):{
		"before_cancel":"finbyzerp.api.po_so_before_cancel",
	},
	("Pick List","Expense Claim", "Sales Invoice", "Purchase Invoice", "Payment Request", "Payment Entry", "Journal Entry", "Material Request", "Purchase Order", "Work Order", "Production Plan", "Stock Entry", "Quotation", "Sales Order", "Delivery Note", "Purchase Receipt", "Packing Slip","Jobwork Challan","Jobwork Finish","Outward Sample","Inward Sample","Manufacturing Consumption","Credit and Debit Note","Outward Tracking","Sample Requirement","Proforma Invoice","Mould Trail Request", "Work Order Master", "Asset", "Leave Application" , "Contract Term"): {
		"before_naming": "finbyzerp.api.before_naming",
	},
	"Purchase Order": {
        "validate": "finbyzerp.finbyzerp.doc_events.payment_entry.validate",
        "on_update_after_submit": "finbyzerp.finbyzerp.doc_events.payment_entry.on_update_after_submit",
	},
    "Payment Entry": {
        "validate": "finbyzerp.finbyzerp.doc_events.purchase_order.validate",
        "on_update_after_submit": "finbyzerp.finbyzerp.doc_events.purchase_order.on_update_after_submit",
	},
	"Form Tour": {
		"before_save":"finbyzerp.finbyzerp.doc_events.form_tour.before_save",
		"on_update":"finbyzerp.finbyzerp.doc_events.form_tour.on_update"
	},
	("Quotation","Sales Order","Delivery Note","Sales Invoice"):{
			"on_submit":"finbyzerp.finbyzerp.doc_events.quotation.on_submit",
			"before_update_after_submit":"finbyzerp.finbyzerp.doc_events.quotation.before_update_after_submit",
			"before_cancel":"finbyzerp.finbyzerp.doc_events.quotation.on_cancel",
			"on_trash":"finbyzerp.finbyzerp.doc_events.quotation.on_trash"
		},
    "Sales Order": {
        "validate": "finbyzerp.finbyzerp.doc_events.sales_order.validate",
        "on_update_after_submit": "finbyzerp.finbyzerp.doc_events.sales_order.on_update_after_submit",
	},
    "Stock Settings":{
        "validate":"finbyzerp.api.create_property_setter"
	}
}

scheduler_events = {
	"cron":{
# 		"*/5 * * * *":[
# 			"finbyzerp.api.repost_transaction_entries"
# 		],
		"0 4 * * SUN": [
			"finbyzerp.api.sales_invoice_payment_remainder",
		]
	},
	"daily":[
		"finbyzerp.api.daily_entry_summary_mail",
		"finbyzerp.api.daily_transaction_summary_mail"
	]
}

# BOM Stock Calculated Report Override:
# from finbyzerp.finbyzerp.report.bom_stock_calculated import execute as bsc_execute
# from erpnext.manufacturing.report.bom_stock_calculated import bom_stock_calculated
# bom_stock_calculated.execute = bsc_execute

from frappe.utils import pdf
from finbyzerp.print_format import get_pdf
pdf.get_pdf = get_pdf


from finbyzerp.finbyzerp.report.stock_ledger import execute as stock_ledger_execute
from erpnext.stock.report.stock_ledger import stock_ledger
stock_ledger.execute = stock_ledger_execute

from finbyzerp.finbyzerp.report.stock_balance import execute as stock_balance_execute
from erpnext.stock.report.stock_balance import stock_balance
stock_balance.execute = stock_balance_execute


from finbyzerp.finbyzerp.report.trial_balance_for_party import execute as trial_balance_for_party_execute
from erpnext.accounts.report.trial_balance_for_party import trial_balance_for_party
trial_balance_for_party.execute = trial_balance_for_party_execute

# Override Stock and Accounts diff validation for throw when amount is > 5
from erpnext.accounts import utils
from finbyzerp.api import check_if_stock_and_account_balance_synced
utils.check_if_stock_and_account_balance_synced = check_if_stock_and_account_balance_synced

from frappe import utils
from finbyzerp.api import get_timespan_date_range
utils.get_timespan_date_range = get_timespan_date_range

from frappe.model import db_query
from finbyzerp.api import get_date_range
db_query.get_date_range = get_date_range

# from india_compliance.gst_india.report.gstr_1.gstr_1 import Gstr1Report
# from finbyzerp.finbyzerp.override.gstr_1 import get_items_based_on_tax_rate as get_items_based_on_tax_rate_custom
# from finbyzerp.finbyzerp.override.gstr_1 import get_row_data_for_invoice as get_row_data_for_invoice_custom
# Gstr1Report.get_row_data_for_invoice = get_row_data_for_invoice_custom
# Gstr1Report.get_items_based_on_tax_rate = get_items_based_on_tax_rate_custom

# from frappe.workflow.doctype.workflow_action import workflow_action
# from finbyzerp.api import process_workflow_actions
# workflow_action.process_workflow_actions = process_workflow_actions

from erpnext.accounts import general_ledger
from finbyzerp.finbyzerp.override.general_ledger import check_freezing_date , get_result_as_list
general_ledger.check_freezing_date = check_freezing_date


from erpnext.accounts.report.general_ledger  import  general_ledger
from finbyzerp.finbyzerp.override.general_ledger import execute
general_ledger.execute = execute
general_ledger.get_result_as_list  = get_result_as_list

from erpnext.stock.doctype.stock_ledger_entry.stock_ledger_entry import StockLedgerEntry
from finbyzerp.finbyzerp.override.stock_ledger_entry import check_stock_frozen_date
StockLedgerEntry.check_stock_frozen_date = check_stock_frozen_date

from finbyzerp.finbyzerp.report.sales_order_analysis import execute as sales_order_analysis_execute
from erpnext.selling.report.sales_order_analysis import sales_order_analysis
sales_order_analysis.execute = sales_order_analysis_execute

from finbyzerp.finbyzerp.report.pending_so_items_for_purchase_request import execute as pending_so_items_for_purchase_request_execute
from erpnext.selling.report.pending_so_items_for_purchase_request import pending_so_items_for_purchase_request
pending_so_items_for_purchase_request.execute = pending_so_items_for_purchase_request_execute

from finbyzerp.finbyzerp.report.trends import get_data as trends_data
from erpnext.controllers import trends
trends.get_data = trends_data

from erpnext.controllers import sales_and_purchase_return
from finbyzerp.api import validate_returned_items
sales_and_purchase_return.validate_returned_items = validate_returned_items

fixtures = [
       {
         "dt": "Custom Field", 
         "filters":[["module", "in", ['Finbyzerp']]]
      },
]

from india_compliance.gst_india.api_classes.returns import PublicCertificate
from india_compliance.gst_india.api_classes.returns import FilesAPI
from india_compliance.gst_india.api_classes.returns import ReturnsAPI
from india_compliance.gst_india.api_classes.e_invoice import EInvoiceAPI
from finbyzerp.e_invoice_override_14 import einvoice_setup
from finbyzerp.returns import get_gstn_public_certificate, returns_api_setup

PublicCertificate.get_gstn_public_certificate = get_gstn_public_certificate
FilesAPI.BASE_PATH = "gstn/files"
ReturnsAPI.SENSITIVE_INFO = ReturnsAPI.SENSITIVE_INFO + ('authorization',)
ReturnsAPI.BASE_PATH = "gstn"
ReturnsAPI.setup = returns_api_setup
EInvoiceAPI.setup = einvoice_setup

from india_compliance.gst_india.api_classes.e_waybill import EWaybillAPI
from finbyzerp.e_invoice_override_14 import ewaybill_setup
EWaybillAPI.setup = ewaybill_setup

from india_compliance.gst_india.api_classes.base import BaseAPI
from finbyzerp.e_invoice_override_14 import get_url
BaseAPI.get_url = get_url

from india_compliance.gst_india.api_classes.public import PublicAPI
from finbyzerp.e_invoice_override_14 import get_gstin_info
PublicAPI.get_gstin_info = get_gstin_info 

from india_compliance.gst_india.utils.transaction_data import GSTTransactionData
from finbyzerp.e_invoice_override_14 import update_transaction_tax_details as new_update_transaction_tax_details
GSTTransactionData.update_transaction_tax_details = new_update_transaction_tax_details

# Override Trends Reports
from erpnext.selling.report.sales_order_trends import sales_order_trends
from finbyzerp.sales_order_trends import sales_order_trends_execute
sales_order_trends.execute = sales_order_trends_execute

from erpnext.stock.report.delivery_note_trends import delivery_note_trends
from finbyzerp.delivery_note_trends import delivery_note_trends_execute
delivery_note_trends.execute = delivery_note_trends_execute

from erpnext.accounts.report.sales_invoice_trends import sales_invoice_trends
from finbyzerp.sales_invoice_trends import sales_invoice_trends_execute
sales_invoice_trends.execute = sales_invoice_trends_execute

from erpnext.buying.report.purchase_order_trends import purchase_order_trends
from finbyzerp.purchase_order_trends import purchse_order_trends_execute
purchase_order_trends.execute = purchse_order_trends_execute

from erpnext.stock.report.purchase_receipt_trends import purchase_receipt_trends
from finbyzerp.purchase_receipt_trends import purchase_receipt_trends_execute
purchase_receipt_trends.execute = purchase_receipt_trends_execute

from erpnext.accounts.report.purchase_invoice_trends import purchase_invoice_trends
from finbyzerp.purchase_invoice_trends import purchase_invoice_trends_execute
purchase_invoice_trends.execute = purchase_invoice_trends_execute

from erpnext.controllers.buying_controller import BuyingController
from finbyzerp.api import set_qty_as_per_stock_uom
BuyingController.set_qty_as_per_stock_uom = set_qty_as_per_stock_uom

from erpnext.buying.report.purchase_order_analysis import purchase_order_analysis
from finbyzerp.purchase_order_analysis import get_data
purchase_order_analysis.get_data = get_data

from india_compliance.gst_india.overrides import transaction
from finbyzerp.finbyzerp.transaction import validate_gst_accounts
transaction.validate_gst_accounts = validate_gst_accounts

from india_compliance.gst_india.overrides.transaction import ItemGSTTreatment
from finbyzerp.finbyzerp.transaction import set_for_no_taxes as _set_for_no_taxes
ItemGSTTreatment.set_for_no_taxes = _set_for_no_taxes