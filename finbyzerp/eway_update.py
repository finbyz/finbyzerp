import json
import frappe, re
from frappe.utils import flt
from erpnext.regional.india.utils import validate_sales_invoice, get_address_details, get_gst_accounts, get_transport_details
from erpnext.controllers.taxes_and_totals import get_itemised_tax, get_itemised_taxable_amount

def get_itemised_tax_breakup_data(doc, account_wise=False, eway=False):
	itemised_tax = get_itemised_tax(doc.taxes, with_tax_account=account_wise)
	
	itemised_taxable_amount = get_itemised_taxable_amount(doc.items)

	account_list = []
	gst_setting = frappe.get_single("GST Settings")
	for row in gst_setting.gst_accounts:
		if row.company == doc.company:
			account_list.append(row.cgst_account)
			account_list.append(row.sgst_account)
			account_list.append(row.igst_account)
			account_list.append(row.cess_account)
			account_list.append(row.tcs_account)

	for key, value in itemised_taxable_amount.items():
		for taxes in frappe.get_list("Sales Taxes and Charges", {'parent': doc.name}, '*'):
			if taxes.account_head not in account_list:
				iwtd = json.loads(taxes.item_wise_tax_detail)
				itemised_taxable_amount[key] += iwtd[key][1]

	if eway == True:
		qty = 0
		qtyUnit = None
		for d in doc.items:
			if hasattr("Item Group",'gst_item_name'):
				item_name = frappe.db.get_value("Item Group", d.item_group, 'gst_item_name') or d.item_group
			else:
				item_name = d.item_group
			qty += d.qty
			qtyUnit = d.uom

	if not frappe.get_meta(doc.doctype + " Item").has_field('gst_hsn_code'):
		if eway == False:
			return itemised_tax, itemised_taxable_amount
		else:
			return itemised_tax, itemised_taxable_amount, item_name, qty, qtyUnit

	item_hsn_map = frappe._dict()
	for d in doc.items:
		item_hsn_map.setdefault(d.item_code or d.item_name, d.get("gst_hsn_code"))

	hsn_tax = {}
	for item, taxes in itemised_tax.items():
		hsn_code = item_hsn_map.get(item)
		hsn_tax.setdefault(hsn_code, frappe._dict())
		for tax_desc, tax_detail in taxes.items():
			key = tax_desc
			if account_wise:
				key = tax_detail.get('tax_account')
			hsn_tax[hsn_code].setdefault(key, {"tax_rate": 0, "tax_amount": 0})
			hsn_tax[hsn_code][key]["tax_rate"] = tax_detail.get("tax_rate")
			hsn_tax[hsn_code][key]["tax_amount"] += tax_detail.get("tax_amount")

	# set taxable amount
	hsn_taxable_amount = frappe._dict()
	for item in itemised_taxable_amount:
		hsn_code = item_hsn_map.get(item)
		hsn_taxable_amount.setdefault(hsn_code, 0)
		hsn_taxable_amount[hsn_code] += itemised_taxable_amount.get(item)

	if eway == False:
		return hsn_tax, hsn_taxable_amount
	else:
		return hsn_tax, hsn_taxable_amount, item_name, qty, qtyUnit

def get_item_list(data, doc):
	for attr in ['cgstValue', 'sgstValue', 'igstValue', 'cessValue', 'OthValue']:
		data[attr] = 0

	gst_accounts = get_gst_accounts(doc.company, account_wise=True)
	tax_map = {
		'sgst_account': ['sgstRate', 'sgstValue'],
		'cgst_account': ['cgstRate', 'cgstValue'],
		'igst_account': ['igstRate', 'igstValue'],
		'cess_account': ['cessRate', 'cessValue'],
	}
	item_data_attrs = ['sgstRate', 'cgstRate', 'igstRate', 'cessRate', 'cessNonAdvol']
	hsn_wise_charges, hsn_taxable_amount, item_name, qty, qtyUnit = get_itemised_tax_breakup_data(doc, account_wise=True, eway=True)
	# frappe.throw(str(hsn_wise_charges))
	for hsn_code, taxable_amount in hsn_taxable_amount.items():
		item_data = frappe._dict()
		if not hsn_code:
			frappe.throw(_('GST HSN Code does not exist for one or more items'))
		item_data.hsnCode = int(hsn_code)
		item_data.taxableAmount = round(taxable_amount,2)
		item_data.productName = item_name
		item_data.productDesc = item_name
		item_data.quantity = round(qty,2)
		item_data.qtyUnit = qtyUnit
		
		for attr in item_data_attrs:
			item_data[attr] = 0

		for account, tax_detail in hsn_wise_charges.get(hsn_code, {}).items():
			account_type = gst_accounts.get(account, '')
			for tax_acc, attrs in tax_map.items():
				if account_type == tax_acc:
					item_data[attrs[0]] = tax_detail.get('tax_rate')
					data[attrs[1]] += tax_detail.get('tax_amount')
					break
			else:
				data.OthValue += tax_detail.get('tax_amount')


		data.itemList.append(item_data)

		# Tax amounts rounded to 2 decimals to avoid exceeding max character limit
		for attr in ['sgstValue', 'cgstValue', 'igstValue', 'cessValue']:
			data[attr] = flt(data[attr], 2)
		#data['totalValue'] += item_data.taxableAmount
	return data

# No change in this function
def get_ewb_data(dt, dn):
	if dt != 'Sales Invoice':
		frappe.throw(_('e-Way Bill JSON can only be generated from Sales Invoice'))

	ewaybills = []
	for doc_name in dn:
		doc = frappe.get_doc(dt, doc_name)

		validate_sales_invoice(doc)

		data = frappe._dict({
			"transporterId": "",
			"TotNonAdvolVal": 0,
		})

		data.userGstin = data.fromGstin = doc.company_gstin
		data.supplyType = 'O'

		if doc.gst_category in ['Registered Regular', 'SEZ']:
			data.subSupplyType = 1
		elif doc.gst_category in ['Overseas', 'Deemed Export']:
			data.subSupplyType = 3
		else:
			frappe.throw(_('Unsupported GST Category for e-Way Bill JSON generation'))

		data.docType = 'INV'
		data.docDate = frappe.utils.formatdate(doc.posting_date, 'dd/mm/yyyy')

		company_address = frappe.get_doc('Address', doc.company_address)
		billing_address = frappe.get_doc('Address', doc.customer_address)

		shipping_address = frappe.get_doc('Address', doc.shipping_address_name)

		data = get_address_details(data, doc, company_address, billing_address)

		data.itemList = []
		data.totalValue = 0

		data = get_item_list(data, doc)
		disable_rounded = frappe.db.get_single_value('Global Defaults', 'disable_rounded_total')
		data.totInvValue = doc.grand_total if disable_rounded else doc.rounded_total
		#finbyz Changes
		data.totalValue = doc.gst_taxable_value
		data.OthValue = round(data.totInvValue - data.totalValue - (data.cgstValue + data.igstValue + data.sgstValue + data.cessValue),2)
		#finbyz changes end
		data = get_transport_details(data, doc)

		fields = {
			"/. -": {
				'docNo': doc.name,
				'fromTrdName': doc.company,
				'toTrdName': doc.customer_name,
				'transDocNo': doc.lr_no,
			},
			"@#/,&. -": {
				'fromAddr1': company_address.address_line1,
				'fromAddr2': company_address.address_line2,
				'fromPlace': company_address.city,
				'toAddr1': shipping_address.address_line1,
				'toAddr2': shipping_address.address_line2,
				'toPlace': shipping_address.city,
				'transporterName': doc.transporter_name
			}
		}

		for allowed_chars, field_map in fields.items():
			for key, value in field_map.items():
				if not value:
					data[key] = ''
				else:
					data[key] = re.sub(r'[^\w' + allowed_chars + ']', '', value)

		ewaybills.append(data)

	data = {
		'version': '1.0.0421', # Finbyz change
		'billLists': ewaybills
	}

	return data


@frappe.whitelist()
def generate_ewb_json(dt, dn):
	dn = json.loads(dn)
	return get_ewb_data(dt, dn)

@frappe.whitelist()
def download_ewb_json():
	data = frappe._dict(frappe.local.form_dict)

	frappe.local.response.filecontent = json.dumps(json.loads(data['data']), indent=4, sort_keys=True)
	frappe.local.response.type = 'download'

	billList = json.loads(data['data'])['billLists']

	if len(billList) > 1:
		doc_name = 'Bulk'
	else:
		doc_name = data['docname']

	frappe.local.response.filename = '{0}_e-WayBill_Data_{1}.json'.format(doc_name, frappe.utils.random_string(5))