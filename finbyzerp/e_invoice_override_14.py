import frappe, json, re
from frappe import _, bold
from frappe.utils import cstr, cint, flt, getdate, format_date
import base64
import os
import jwt
from frappe.utils import now_datetime
from urllib.parse import urlencode, urljoin
from frappe.utils.data import time_diff_in_seconds
from india_compliance.gst_india.utils import load_doc
from india_compliance.gst_india.utils.e_waybill import (
    _cancel_e_waybill,
    log_and_process_e_waybill_generation,
)
from india_compliance.gst_india.utils.e_invoice import log_e_invoice
from india_compliance.gst_india.utils.e_invoice import EInvoiceData
from india_compliance.gst_india.api_classes.e_invoice import EInvoiceAPI
from frappe.utils.data import add_to_date
from india_compliance.gst_india.utils import parse_datetime, send_updated_doc
# from erpnext.regional.india.e_invoice.utils import (GSPConnector,raise_document_name_too_long_error,read_json,
# 	validate_mandatory_fields,get_doc_details,get_return_doc_reference,
# 	get_eway_bill_details,validate_totals,show_link_to_error_log,santize_einvoice_fields,safe_json_load,get_payment_details,
# 	validate_eligibility,update_item_taxes,get_invoice_value_details,get_party_details,update_other_charges,
# 	get_overseas_address_details, validate_address_fields, sanitize_for_json, log_error)

from india_compliance.gst_india.utils import get_place_of_supply


GST_INVOICE_NUMBER_FORMAT = re.compile(r"^[a-zA-Z0-9\-/]+$")   #alphanumeric and - /
def validate_document_name(doc, method=None):
	"""Validate GST invoice number requirements."""

	country = frappe.get_cached_value("Company", doc.company, "country")
	einvoice_enable = frappe.db.get_single_value("E Invoice Settings",'enable')
	# Date was chosen as start of next FY to avoid irritating current users.
	if country != "India" or getdate(doc.posting_date) < getdate("2021-04-01"):
		return
	
	if len(doc.name) > 14 and not frappe.db.get_single_value("System Settings",'disable_invoice_length_check') and not doc.amended_from:
		frappe.throw(_(f"For GST fillings Invoice name should be less than 16 digits, to keep scope of amened documents please ensure invoice number doesn't go beyond 14 digits {doc.name}"))

	if einvoice_enable and len(doc.name) > 16:
		frappe.throw(_("Maximum length of document number should be 16 characters as per GST rules. Please change the naming series."))

	if not GST_INVOICE_NUMBER_FORMAT.match(doc.name):
		frappe.throw(_("Document name should only contain alphanumeric values, dash(-) and slash(/) characters as per GST rules. Please change the naming series."))

def validate_invoice_number(doc):
	"""Validate GST invoice number requirements."""
	
	if len(doc.name) > 14 and not frappe.db.get_single_value("System Settings",'disable_invoice_length_check') and not doc.amended_from:
		frappe.throw(_(f"For GST fillings Invoice name should be less than 16 digits, to keep scope of amened documents please ensure invoice number doesn't go beyond 14 digits {doc.name}"))

	if len(doc.name) > 16:
		frappe.throw(
			_("GST Invoice Number cannot exceed 16 characters"),
			title=_("Invalid GST Invoice Number"),
		)

	if not GST_INVOICE_NUMBER_FORMAT.match(doc.name):
		frappe.throw(
			_(
				"GST Invoice Number should start with an alphanumeric character and can"
				" only contain alphanumeric characters, dash (-) and slash (/)"
			),
			title=_("Invalid GST Invoice Number"),
		)

def validate_einvoice_fields(doc):
	invoice_eligible = validate_eligibility(doc)

	if not invoice_eligible:
		return

	# Finbyz Changes Start: dont change posting date and sales taxes and charges table after irn generated
	if doc.irn and doc.docstatus == 0:
		doc.set_posting_time = 1
		if str(doc.posting_date) != str(frappe.db.get_value("Sales Invoice",doc.name,"posting_date")):
			frappe.throw(_('You cannot edit the invoice after generating IRN'), title=_('Edit Not Allowed'))
		if str(len(doc.taxes)) != str(len(frappe.db.get_all("Sales Taxes and Charges",{'parent':doc.name,'parenttype':doc.doctype}))):
			frappe.throw(_('You cannot edit the invoice after generating IRN'), title=_('Edit Not Allowed'))
	# Finbyz Changes End
	if doc.docstatus == 0 and doc._action == 'save':
		if doc.irn and not doc.eway_bill_cancelled and doc.grand_total != frappe.db.get_value("Sales Invoice",doc.name,"grand_total"):# Finbyz Changes:
			frappe.throw(_('You cannot edit the invoice after generating IRN'), title=_('Edit Not Allowed'))
		if len(doc.name) > 16:
			raise_document_name_too_long_error()

	elif doc.docstatus == 1 and doc._action == 'submit' and not doc.irn and doc.irn_cancelled == 0: # finbyz 
		frappe.throw(_('You must generate IRN before submitting the document.'), title=_('Missing IRN'))

	elif doc.irn and doc.docstatus == 2 and doc._action == 'cancel' and not doc.irn_cancelled:
		frappe.throw(_('You must cancel IRN before cancelling the document.'), title=_('Cancel Not Allowed'))

def get_transaction_details(invoice):
	supply_type = ''
	if invoice.gst_category == 'Registered Regular': supply_type = 'B2B'
	elif invoice.gst_category == 'SEZ': supply_type = 'SEZWOP'
	# elif invoice.gst_category == 'Overseas': supply_type = 'EXPWOP'
	elif invoice.gst_category == 'Overseas' and invoice.export_type == "Without Payment of Tax": supply_type = 'EXPWOP' # Finbyz Changes
	elif invoice.gst_category == 'Overseas' and invoice.export_type == "With Payment of Tax": supply_type = 'EXPWP' # Finbyz Changes
	elif invoice.gst_category == 'Deemed Export': supply_type = 'DEXP'

	if not supply_type:
		rr, sez, overseas, export = bold('Registered Regular'), bold('SEZ'), bold('Overseas'), bold('Deemed Export')
		frappe.throw(_('GST category should be one of {}, {}, {}, {}').format(rr, sez, overseas, export),
			title=_('Invalid Supply Type'))

	return frappe._dict(dict(
		tax_scheme='GST',
		supply_type=supply_type,
		reverse_charge=invoice.reverse_charge
	))


def make_einvoice(invoice):
	validate_mandatory_fields(invoice)

	schema = read_json('einv_template')

	transaction_details = get_transaction_details(invoice)
	item_list = get_item_list(invoice)
	doc_details = get_doc_details(invoice)
	invoice_value_details = get_invoice_value_details(invoice)
	seller_details = get_party_details(invoice.company_address)

	if invoice.gst_category == 'Overseas':
		buyer_details = get_overseas_address_details(invoice.customer_address)
	else:
		buyer_details = get_party_details(invoice.customer_address)
		place_of_supply = get_place_of_supply(invoice, invoice.doctype)
		if place_of_supply:
			place_of_supply = place_of_supply.split('-')[0]
		else:
			place_of_supply = sanitize_for_json(invoice.billing_address_gstin)[:2]
		buyer_details.update(dict(place_of_supply=place_of_supply))

	seller_details.update(dict(legal_name=invoice.company))
	buyer_details.update(dict(legal_name=invoice.customer_name or invoice.customer))

	shipping_details = payment_details = prev_doc_details = eway_bill_details = frappe._dict({})
	if invoice.shipping_address_name and invoice.customer_address != invoice.shipping_address_name:
		if invoice.gst_category == 'Overseas':
			shipping_details = get_overseas_address_details(invoice.shipping_address_name)
		else:
			shipping_details = get_party_details(invoice.shipping_address_name, skip_gstin_validation=True)

	# Finbyz Changes START: If Export Invoice then For Eway Bill generation Ship to Details Are Mandatory and Ship To Pincode and Ship to State Code Should be Pincode and State Code of Port/Place From India
	# In case of export transactions for goods, if e-way bill is required along with IRN, then the 'Ship-To' address should be of the place/port in India from where the goods are being exported. Otherwise E-way bill can be generated later based on IRN, by passing the 'Ship-To' address as the place/port address of India from where the goods are being exported .
	if invoice.get("eway_bill_ship_to_address") and invoice.gst_category == "Overseas":
		shipping_details = get_port_address_details(invoice.eway_bill_ship_to_address, skip_gstin_validation=True)
	# Finbyz Changes END

	dispatch_details = frappe._dict({})
	if invoice.dispatch_address_name:
		dispatch_details = get_party_details(invoice.dispatch_address_name, skip_gstin_validation=True)

	if invoice.is_pos and invoice.base_paid_amount:
		payment_details = get_payment_details(invoice)

	if invoice.is_return and invoice.return_against:
		prev_doc_details = get_return_doc_reference(invoice)

	if invoice.transporter and not invoice.is_return:
		eway_bill_details = get_eway_bill_details(invoice)

	# not yet implemented
	period_details = export_details = frappe._dict({})

	einvoice = schema.format(
		transaction_details=transaction_details, doc_details=doc_details, dispatch_details=dispatch_details,
		seller_details=seller_details, buyer_details=buyer_details, shipping_details=shipping_details,
		item_list=item_list, invoice_value_details=invoice_value_details, payment_details=payment_details,
		period_details=period_details, prev_doc_details=prev_doc_details,
		export_details=export_details, eway_bill_details=eway_bill_details
	)

	try:
		einvoice = safe_json_load(einvoice)
		einvoice = santize_einvoice_fields(einvoice)
	except Exception:
		show_link_to_error_log(invoice, einvoice)

	try:
		validate_totals(einvoice)
	except Exception:
		log_error(einvoice)
		raise

	return einvoice

def get_item_list(self):
	self.item_list = []

	for row in self.doc.items:
		uom = row.uom.upper()

		item_details = frappe._dict(
			{
				"item_no": row.idx,
				"qty": abs(self.rounded(row.get('quantity') or row.qty, 3)),
				"taxable_value": abs(self.rounded(row.taxable_value)),
				"hsn_code": row.gst_hsn_code,
				"item_name": self.sanitize_value(row.item_name, 3, max_length=300),
				"uom": uom if uom in UOMS else "OTH",
			}
		)
		self.update_item_details(item_details, row)
		self.get_item_tax_details(item_details, row)
		self.item_list.append(self.get_item_data(item_details))

# def get_item_list(invoice):
# 	item_list = []

# 	for d in invoice.items:
# 		einvoice_item_schema = read_json('einv_item_template')
# 		item = frappe._dict({})
# 		item.update(d.as_dict())

# 		item.sr_no = d.idx
# 		item.description = json.dumps(d.item_name)[1:-1]

# 		# Finbyz changes Start: Wherever Quantity is calculating based on concentration with qty 
# 		try:
# 			item.qty = abs(item.quantity)
# 		except:
# 			item.qty = abs(item.qty)
# 		# Finbyz Changes End
		
# 		if invoice.apply_discount_on == 'Net Total' and invoice.discount_amount:
# 			item.discount_amount = abs(item.base_amount - item.base_net_amount)
# 		else:
# 			item.discount_amount = 0

# 		item.unit_rate = abs((abs(item.taxable_value) - item.discount_amount)/ item.qty)
# 		item.gross_amount = abs(item.taxable_value) + item.discount_amount
# 		item.taxable_value = abs(item.taxable_value)

# 		item.batch_expiry_date = frappe.db.get_value('Batch', d.batch_no, 'expiry_date') if d.batch_no else None
# 		item.batch_expiry_date = format_date(item.batch_expiry_date, 'dd/mm/yyyy') if item.batch_expiry_date else None
# 		#finbyz Changes
# 		if frappe.db.get_value('Item', d.item_code, 'is_stock_item') or frappe.db.get_value('Item', d.item_code, 'is_not_service_item'):
# 			item.is_service_item = 'N'  
# 		else:
# 			item.is_service_item = 'Y'
# 		#finbyz changes end
		
# 		item.serial_no = ""

# 		item = update_item_taxes(invoice, item)
		
# 		item.total_value = abs(
# 			item.taxable_value + item.igst_amount + item.sgst_amount +
# 			item.cgst_amount + item.cess_amount + item.cess_nadv_amount + item.other_charges
# 		)
# 		einv_item = einvoice_item_schema.format(item=item)
# 		item_list.append(einv_item)

# 	return ', '.join(item_list)

def get_port_address_details(address_name, skip_gstin_validation):
	addr = frappe.get_doc('Address', address_name)

	validate_address_fields(addr, skip_gstin_validation= skip_gstin_validation)

	return frappe._dict(dict(
		gstin='URP',
		legal_name=sanitize_for_json(addr.address_title),
		location=addr.city,
		address_line1=sanitize_for_json(addr.address_line1),
		address_line2=sanitize_for_json(addr.address_line2),
		pincode= addr.pincode, state_code= addr.gst_state_number
	))


@frappe.whitelist()
def cancel_eway_bill(doctype, docname, eway_bill, reason, remark):
	gsp_connector = GSPConnector(doctype, docname)
	gsp_connector.cancel_eway_bill(eway_bill, reason, remark)


# E invoice Override for custom API integration
from frappe.integrations.utils import make_request
from frappe.utils.password import get_decrypted_password

def einvoice_setup(self, doc=None, *, company_gstin=None):
	self.BASE_PATH = "enriched/ei/api"
	if not self.settings.enable_e_invoice:
		frappe.throw(_("Please enable e-Waybill features in GST Settings first"))
	self.gst_settings = frappe.get_cached_doc("GST Settings")
	if doc:
		company_gstin = doc.company_gstin
		self.default_log_values.update(
			reference_doctype=doc.doctype,
			reference_name=doc.name,
		)

	if self.sandbox_mode:
		company_gstin = "05AAACG2115R1ZN"
		self.username = "05AAACG2115R1ZN"
		self.password = "abc123@@"

	elif not company_gstin:
		frappe.throw(_("Company GSTIN is required to use the e-Waybill API"))

	else:
		self.fetch_credentials(company_gstin, "e-Waybill / e-Invoice")

	self.default_headers.update(
		{
			"authorization": get_auth_token(self),
			"gstin": company_gstin,
			"user_name": self.username,
			"password": self.password,
			"requestid": str(base64.b64encode(os.urandom(18))),
		}
	)
	
def ewaybill_setup(self, doc=None, *, company_gstin=None):
	self.gst_settings = frappe.get_cached_doc("GST Settings")
	self.BASE_PATH = "enriched/ewb/ewayapi"
	if not self.settings.enable_e_waybill:
		frappe.throw(_("Please enable e-Waybill features in GST Settings first"))

	if doc:
		company_gstin = doc.company_gstin
		self.default_log_values.update(
			reference_doctype=doc.doctype,
			reference_name=doc.name,
		)

	if self.sandbox_mode:
		company_gstin = "05AAACG2115R1ZN"
		self.username = "05AAACG2115R1ZN"
		self.password = "abc123@@"

	elif not company_gstin:
		frappe.throw(_("Company GSTIN is required to use the e-Waybill API"))

	else:
		self.fetch_credentials(company_gstin, "e-Waybill / e-Invoice")

	self.default_headers.update(
		{
			"authorization": get_auth_token(self),
			"gstin": company_gstin,
			"username": self.username,
			"password": self.password,
			"requestid": str(base64.b64encode(os.urandom(18))),
		}
	)

def get_auth_token(self):
	if not hasattr(self, "gst_settings"):
		self.gst_settings = frappe.get_cached_doc("GST Settings")
	if time_diff_in_seconds(self.gst_settings.token_expiry, now_datetime()) < 150.0 or not self.gst_settings.auth_token:
		fetch_auth_token(self)

	return self.gst_settings.auth_token
	
def get_client_details(self):
	if self.gst_settings.get('client_id') and self.gst_settings.get('client_secret'):
		return self.gst_settings.get('client_id'), get_decrypted_password("GST Settings", "GST Settings", fieldname = "client_secret")

	return frappe.conf.einvoice_client_id, frappe.conf.einvoice_client_secret

def fetch_auth_token(self):
	client_id, client_secret = get_client_details(self)
	headers = {"gspappid": client_id, "gspappsecret": client_secret}
	res = {}
	url = "https://gsp.adaequare.com/gsp/authenticate?grant_type=token"\

	res = make_request("post", url, headers = headers)
	self.gst_settings.auth_token = "{} {}".format(
		res.get("token_type"), res.get("access_token")
	)

	self.gst_settings.token_expiry = add_to_date(None, seconds=res.get("expires_in"))
	self.gst_settings.save(ignore_permissions=True)
	self.gst_settings.reload()

from india_compliance.gst_india.api_classes.base import BaseAPI

# class CustomBaseAPI(BaseAPI):
# 	base_url = "https://gsp.adaequare.com"
def get_url(self, *parts):
	self.base_url = "https://gsp.adaequare.com"
	parts = [i for i in parts if i != '']

	if self.BASE_PATH:
		parts.insert(0, self.BASE_PATH)

	if self.sandbox_mode:
		parts.insert(0, "test")

	return urljoin(self.base_url, "/".join(part.strip("/") for part in parts))

def get_gstin_info(self, gstin):
	self.BASE_PATH = "enriched/commonapi"
	self.gst_settings = frappe.get_cached_doc("GST Settings")
	self.default_headers = {
			"authorization": get_auth_token(self),
			"requestid": str(base64.b64encode(os.urandom(18))),
		}
	return self.get("search", params={"action": "TP", "gstin": gstin})


from india_compliance.gst_india.constants import GST_TAX_TYPES
def update_transaction_tax_details(self):
	tax_total_keys = tuple(f"total_{tax}_amount" for tax in GST_TAX_TYPES)

	for key in tax_total_keys:
		self.transaction_details[key] = 0
	# Finbyz Changes Start
	reverse_charge_account = frappe.db.get_value("GST Account", {'company': self.doc.company, "account_type" : "Output"}, "export_reverse_charge_account")

	reverse_charge_amount = 0
	total_tax_amount = 0

	for row in self.doc.taxes:
		if reverse_charge_account == row.account_head:
			reverse_charge_amount = row.base_tax_amount_after_discount_amount
		# Finbyz Changes End
		if not row.tax_amount or row.account_head not in self.gst_accounts:
			continue

		tax = self.gst_accounts[row.account_head][:-8]
		self.transaction_details[f"total_{tax}_amount"] = abs(
			self.rounded(row.base_tax_amount_after_discount_amount)
		)
		total_tax_amount += self.transaction_details[f"total_{tax}_amount"]

	# Other Charges
	current_total = 0
	for key in ("total", "rounding_adjustment", *tax_total_keys):
		current_total += self.transaction_details.get(key)

	current_total -= self.transaction_details.discount_amount
	other_charges = self.transaction_details.grand_total - current_total

	if reverse_charge_amount < 0 and other_charges < 0:
		other_charges = round(other_charges, 1) - round(reverse_charge_amount, 1)
		self.transaction_details.grand_total += total_tax_amount
		self.transaction_details.grand_total = round(self.transaction_details.grand_total,2)
	if 0 > other_charges > -0.1:
		# other charges cannot be negative
		# handle cases where user has higher precision than 2
		self.transaction_details.rounding_adjustment = self.rounded(
			self.transaction_details.rounding_adjustment + other_charges
		)
	else:
		self.transaction_details.other_charges = round(other_charges,2)
