import frappe
import re
import jwt
from frappe import _
from frappe.utils.data import cstr, cint, flt
from erpnext.regional.india.e_invoice.utils import (GSPConnector,raise_document_name_too_long_error,read_json,\
	validate_mandatory_fields,get_doc_details,get_overseas_address_details,get_return_doc_reference,\
	get_eway_bill_details,validate_totals,show_link_to_error_log,santize_einvoice_fields,safe_json_load,get_payment_details,\
	validate_eligibility,update_item_taxes,get_invoice_value_details,get_party_details,update_other_charges)

from erpnext.regional.india.utils import get_gst_accounts,get_place_of_supply
import json

# def validate_einvoice_fields(doc):
# 	invoice_eligible = validate_eligibility(doc)

# 	if not invoice_eligible:
# 		return

# 	if doc.docstatus == 0 and doc._action == 'save':
# 		if doc.irn and not doc.eway_bill_cancelled and doc.grand_total != frappe.db.get_value("Sales Invoice",doc.name,"grand_total"):# Finbyz Changes
# 			frappe.throw(_('You cannot edit the invoice after generating IRN'), title=_('Edit Not Allowed'))
# 		if len(doc.name) > 16:
# 			raise_document_name_too_long_error()

# 	elif doc.docstatus == 1 and doc._action == 'submit' and not doc.irn:
# 		frappe.throw(_('You must generate IRN before submitting the document.'), title=_('Missing IRN'))

# 	elif doc.irn and doc.docstatus == 2 and doc._action == 'cancel' and not doc.irn_cancelled:
# 		frappe.throw(_('You must cancel IRN before cancelling the document.'), title=_('Cancel Not Allowed'))

# def get_transaction_details(invoice):
# 	supply_type = ''
# 	if invoice.gst_category == 'Registered Regular': supply_type = 'B2B'
# 	elif invoice.gst_category == 'SEZ': supply_type = 'SEZWOP'
# 	elif invoice.gst_category == 'Overseas': supply_type = 'EXPWOP'
# 	elif invoice.gst_category == 'Deemed Export': supply_type = 'DEXP'

# 	if not supply_type: 
# 		rr, sez, overseas, export = bold('Registered Regular'), bold('SEZ'), bold('Overseas'), bold('Deemed Export')
# 		frappe.throw(_('GST category should be one of {}, {}, {}, {}').format(rr, sez, overseas, export),
# 			title=_('Invalid Supply Type'))

# 	return frappe._dict(dict(
# 		tax_scheme='GST',
# 		supply_type=supply_type,
# 		reverse_charge=invoice.reverse_charge,
# 		ecom_gstin=invoice.ecommerce_gstin,# Finbyz Changes
# 		igst_on_intra=invoice.get('igst_on_intra') or 'N' # Finbyz Changes
# 	))

# def get_item_list(invoice):
# 	item_list = []

# 	for d in invoice.items:
# 		einvoice_item_schema = read_json('einv_item_template')
# 		item = frappe._dict({})
# 		item.update(d.as_dict())

# 		item.sr_no = d.idx
# 		item.description = json.dumps(d.item_name)[1:-1]

# 		item.qty = abs(item.qty)

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

# # def update_item_taxes(invoice, item):
# # 	gst_accounts = get_gst_accounts(invoice.company)
# # 	gst_accounts_list = [d for accounts in gst_accounts.values() for d in accounts if d]
	
# # 	for attr in [
# # 		'tax_rate', 'cess_rate', 'cess_nadv_amount',
# # 		'cgst_amount',  'sgst_amount', 'igst_amount',
# # 		'cess_amount', 'cess_nadv_amount', 'other_charges'
# # 		]:
# # 		item[attr] = 0
# # 	first = 0 # finbyz
# # 	for t in invoice.taxes:
# # 		is_applicable = t.tax_amount and t.account_head in gst_accounts_list
# # 		if is_applicable:
# # 			# this contains item wise tax rate & tax amount (incl. discount)
# # 			item_tax_detail = json.loads(t.item_wise_tax_detail).get(item.item_code)

			
# # 			item_tax_rate = item_tax_detail[0]

# # 			# Finbyz Changes
# # 			if abs(item_tax_detail[1]) > 0:
# # 				item_tax_amount = item.weight * abs(item_tax_detail[1])

# # 				item.gross_amount = item.taxable_value = (item_tax_amount * 100) / item_tax_rate
# # 				if first == 0:
# # 					invoice.gst_taxable_value += abs(item.taxable_value)
				
# # 			first += 1
# # 			# Finbyz Changes End

# # 			if t.account_head in gst_accounts.cess_account:
# # 				item_tax_amount_after_discount = item_tax_detail[1]
# # 				if t.charge_type == 'On Item Quantity':
# # 					item.cess_nadv_amount += abs(item_tax_amount_after_discount)
# # 				else:
# # 					item.cess_rate += item_tax_rate
# # 					item.cess_amount += abs(item_tax_amount_after_discount)

# # 			for tax_type in ['igst', 'cgst', 'sgst']:
# # 				if t.account_head in gst_accounts['{}_account'.format(tax_type)]:
# # 					item.tax_rate += item_tax_rate
# # 					item['{}_amount'.format(tax_type)] += abs(item_tax_amount)

# # 	return item

# def get_invoice_value_details(invoice):
# 	invoice_value_details = frappe._dict(dict())
# 	# finbyz change
# 	invoice_value_details.total_other_taxes = 0
# 	invoice_value_details.base_total_other_taxes = 0
# 	# finbyz change end 

# 	if invoice.apply_discount_on == 'Net Total' and invoice.discount_amount:
# 		# Discount already applied on net total which means on items
# 		invoice_value_details.base_total = abs(sum([i.taxable_value for i in invoice.get('items')]))
# 		invoice_value_details.invoice_discount_amt = 0
# 	elif invoice.apply_discount_on == 'Grand Total' and invoice.discount_amount:
# 		invoice_value_details.invoice_discount_amt = invoice.base_discount_amount
# 		invoice_value_details.base_total = abs(sum([i.taxable_value for i in invoice.get('items')]))
# 	else:
# 		invoice_value_details.base_total = abs(sum([i.taxable_value for i in invoice.get('items')]))
# 		# since tax already considers discount amount
# 		invoice_value_details.invoice_discount_amt = 0

# 	invoice_value_details.round_off = invoice.base_rounding_adjustment
# 	invoice_value_details.base_grand_total = abs(invoice.base_rounded_total) or abs(invoice.base_grand_total)
# 	invoice_value_details.grand_total = abs(invoice.rounded_total) or abs(invoice.grand_total)
	
# 	invoice_value_details = update_invoice_taxes(invoice, invoice_value_details)
	
# 	#finbyz changes 
# 	invoice_value_details.total_other_charges = abs(invoice_value_details.base_grand_total - (invoice_value_details.base_total + invoice_value_details.total_cgst_amt + invoice_value_details.total_sgst_amt + invoice_value_details.total_igst_amt + invoice_value_details.total_cess_amt + invoice_value_details.invoice_discount_amt + invoice_value_details.round_off + invoice_value_details.base_total_other_taxes))

# 	invoice_value_details.base_grand_total -= invoice_value_details.base_total_other_taxes
# 	invoice_value_details.grand_total -= invoice_value_details.total_other_taxes
# 	#finbyz changes end
# 	return invoice_value_details


# def update_invoice_taxes(invoice, invoice_value_details):
# 	gst_accounts = get_gst_accounts(invoice.company)
# 	gst_accounts_list = [d for accounts in gst_accounts.values() for d in accounts if d]

# 	invoice_value_details.total_cgst_amt = 0
# 	invoice_value_details.total_sgst_amt = 0
# 	invoice_value_details.total_igst_amt = 0
# 	invoice_value_details.total_cess_amt = 0
# 	invoice_value_details.total_other_charges = 0
# 	considered_rows = []

# 	for t in invoice.taxes:
# 		tax_amount = t.base_tax_amount if (invoice.apply_discount_on == 'Grand Total' and invoice.discount_amount) \
# 						else t.base_tax_amount_after_discount_amount
# 		if t.account_head in gst_accounts_list:
# 			if t.account_head in gst_accounts.cess_account:
# 				# using after discount amt since item also uses after discount amt for cess calc
# 				invoice_value_details.total_cess_amt += abs(t.base_tax_amount_after_discount_amount)
			
# 			for tax_type in ['igst', 'cgst', 'sgst']:
# 				if t.account_head in gst_accounts['{}_account'.format(tax_type)]:

# 					invoice_value_details['total_{}_amt'.format(tax_type)] += abs(tax_amount)
# 				update_other_charges(t, invoice_value_details, gst_accounts_list, invoice, considered_rows)
# 		#finbyz changes 
# 		else:
# 			export_reverse_charge_account = frappe.db.get_value("GST Account",{'company':invoice.company,"parent": "GST Settings"},'export_reverse_charge_account')
# 			if t.account_head == export_reverse_charge_account:
# 				invoice_value_details.base_total_other_taxes = t.base_tax_amount
# 				invoice_value_details.total_other_taxes = t.tax_amount

# 			else:
# 				invoice_value_details.total_other_charges += abs(t.base_tax_amount_after_discount_amount)
# 		#finbyz changes end
# 	return invoice_value_details

# def make_einvoice(invoice):
# 	validate_mandatory_fields(invoice)

# 	schema = read_json('einv_template')

# 	transaction_details = get_transaction_details(invoice)
# 	item_list = get_item_list(invoice)
# 	doc_details = get_doc_details(invoice)
# 	invoice_value_details = get_invoice_value_details(invoice)
# 	seller_details = get_party_details(invoice.company_address,1)

# 	if invoice.gst_category == 'Overseas':
# 		buyer_details = get_overseas_address_details(invoice.customer_address)
# 	else:
# 		buyer_details = get_party_details(invoice.customer_address)
# 		place_of_supply = get_place_of_supply(invoice, invoice.doctype)
# 		if place_of_supply:
# 			place_of_supply = place_of_supply.split('-')[0]
# 		else:
# 			place_of_supply = invoice.billing_address_gstin[:2]
# 		buyer_details.update(dict(place_of_supply=place_of_supply))

# 	seller_details.update(dict(legal_name=invoice.company))
# 	buyer_details.update(dict(legal_name=invoice.customer_name or invoice.customer))

# 	shipping_details = payment_details = prev_doc_details = eway_bill_details = frappe._dict({})
# 	if invoice.shipping_address_name and invoice.customer_address != invoice.shipping_address_name:
# 		if invoice.gst_category == 'Overseas':
# 			shipping_details = get_overseas_address_details(invoice.shipping_address_name)
# 		else:
# 			shipping_details = get_party_details(invoice.shipping_address_name)
# 			# FinByz Changes start
# 			if not shipping_details.gstin:
# 				shipping_details.gstin = invoice.customer_gstin
# 			# FinByz Changes end

# 	if invoice.is_pos and invoice.base_paid_amount:
# 		payment_details = get_payment_details(invoice)
	
# 	if invoice.is_return and invoice.return_against:
# 		prev_doc_details = get_return_doc_reference(invoice)
	
# 	if invoice.transporter and flt(invoice.distance) and not invoice.is_return:
# 		eway_bill_details = get_eway_bill_details(invoice)
	
# 	# not yet implemented
# 	dispatch_details = period_details = export_details = frappe._dict({})

# 	einvoice = schema.format(
# 		transaction_details=transaction_details, doc_details=doc_details, dispatch_details=dispatch_details,
# 		seller_details=seller_details, buyer_details=buyer_details, shipping_details=shipping_details,
# 		item_list=item_list, invoice_value_details=invoice_value_details, payment_details=payment_details,
# 		period_details=period_details, prev_doc_details=prev_doc_details,
# 		export_details=export_details, eway_bill_details=eway_bill_details
# 	)
	
# 	try:
# 		einvoice = safe_json_load(einvoice)
# 		einvoice = santize_einvoice_fields(einvoice)
# 	except Exception:
# 		show_link_to_error_log(invoice, einvoice)

# 	validate_totals(einvoice)
# 	return einvoice

# # def get_party_details(address_name):
# # 	d = frappe.get_all('Address', filters={'name': address_name}, fields=['*'])[0]
# # 	# finbyz change remove gstin validtion
# # 	if (not d.city
# # 		or not d.pincode
# # 		or not d.address_title
# # 		or not d.address_line1
# # 		or not d.gst_state_number):

# # 		frappe.throw(
# # 			msg=_('Address lines, city, pincode, gstin is mandatory for address {}. Please set them and try again.').format(
# # 				get_link_to_form('Address', address_name)
# # 			),
# # 			title=_('Missing Address Fields')
# # 		)

# # 	if d.gst_state_number == 97:
# # 		# according to einvoice standard
# # 		pincode = 999999

# # 	return frappe._dict(dict(
# # 		gstin=d.gstin, legal_name=d.address_title,
# # 		location=d.city, pincode=d.pincode,
# # 		state_code=d.gst_state_number,
# # 		address_line1=d.address_line1,
# # 		address_line2=d.address_line2
# # 	))

# # def set_einvoice_data(self, res):
# #     enc_signed_invoice = res.get('SignedInvoice')
# #     dec_signed_invoice = jwt.decode(enc_signed_invoice, verify=False)['data']

# #     self.invoice.irn = res.get('Irn')
# #     self.invoice.ewaybill = res.get('EwbNo')
# #     # FinBy change
# #     self.ack_no = res.get('AckNo')
# #     self.ack_date = res.get('AckDt')
# #     # FinBy change end 
# #     self.invoice.signed_einvoice = dec_signed_invoice
# #     self.invoice.signed_qr_code = res.get('SignedQRCode')

# #     self.attach_qrcode_image()

# #     self.invoice.flags.updater_reference = {
# #         'doctype': self.invoice.doctype,
# #         'docname': self.invoice.name,
# #         'label': _('IRN Generated')
# #     }
# #     self.update_invoice()

def get_item_list(invoice):
	item_list = []

	for d in invoice.items:
		einvoice_item_schema = read_json('einv_item_template')
		item = frappe._dict({})
		item.update(d.as_dict())

		item.sr_no = d.idx
		item.description = json.dumps(d.item_name)[1:-1]

		item.qty = abs(item.qty)

		if invoice.apply_discount_on == 'Net Total' and invoice.discount_amount:
			item.discount_amount = abs(item.base_amount - item.base_net_amount)
		else:
			item.discount_amount = 0

		item.unit_rate = abs((abs(item.taxable_value) - item.discount_amount)/ item.qty)
		item.gross_amount = abs(item.taxable_value) + item.discount_amount
		item.taxable_value = abs(item.taxable_value)

		item.batch_expiry_date = frappe.db.get_value('Batch', d.batch_no, 'expiry_date') if d.batch_no else None
		item.batch_expiry_date = format_date(item.batch_expiry_date, 'dd/mm/yyyy') if item.batch_expiry_date else None
		#finbyz Changes
		if frappe.db.get_value('Item', d.item_code, 'is_stock_item') or frappe.db.get_value('Item', d.item_code, 'is_not_service_item'):
			item.is_service_item = 'N'  
		else:
			item.is_service_item = 'Y'
		#finbyz changes enditem.serial_no = ""

		item = update_item_taxes(invoice, item)
		
		item.total_value = abs(
			item.taxable_value + item.igst_amount + item.sgst_amount +
			item.cgst_amount + item.cess_amount + item.cess_nadv_amount + item.other_charges
		)
		einv_item = einvoice_item_schema.format(item=item)
		item_list.append(einv_item)

	return ', '.join(item_list)

def validate_einvoice_fields(doc):
	invoice_eligible = validate_eligibility(doc)

	if not invoice_eligible:
		return

	# Finbyz Changes Start: dont change posting date after irn generated
	if doc.irn and doc.docstatus == 0 and doc._action == 'save':
		if doc.posting_date != frappe.db.get_value("Sales Invoice",doc.name,"posting_date"):
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

@frappe.whitelist()
def cancel_eway_bill(doctype, docname, eway_bill, reason, remark):
	gsp_connector = GSPConnector(doctype, docname)
	gsp_connector.cancel_eway_bill(eway_bill, reason, remark)
