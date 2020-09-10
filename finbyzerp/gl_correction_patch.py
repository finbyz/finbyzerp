
# Copyright (c) 2013, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.general_ledger import make_gl_entries, delete_gl_entries
# import frappe

	
def patch():
	#data = get_data()
	data =[{'voucher_type': 'Delivery Note', 'voucher_no': 'DN20212100416', 'company': 'Millennium Vitrified Tiles Pvt. Ltd. Testing', 'gl_value': -965770.0, 'value_diff': -869193.0},
	{'voucher_type': 'Stock Entry', 'voucher_no': 'SE20212101584', 'company': 'Millennium Vitrified Tiles Pvt. Ltd. Testing', 'gl_value': -965770.0, 'value_diff': -869193.0}]
	print(data)
	for row in data:
		if row['voucher_type'] in ["Stock Entry","Stock Reconciliation"]:
			se_doc = frappe.get_doc("Stock Entry",row['voucher_no'])
			print(se_doc.name)
			delete_gl_entries(voucher_type=row['voucher_type'],voucher_no=row['voucher_no'])
			se_doc.make_gl_entries(repost_future_gle=False, from_repost=False)
		if row['voucher_type'] == "Payment Entry":
			pe_doc = frappe.get_doc("Payment Entry",row['voucher_no'])
			print(pe_doc.name)
			pe_doc.make_gl_entries(cancel=1)
			pe_doc.make_gl_entries(cancel=0)
		if row['voucher_type'] == "Delivery Note":
			dn_doc = frappe.get_doc("Delivery Note",row['voucher_no'])
			print(dn_doc.name)
			delete_gl_entries(voucher_type=row['voucher_type'],voucher_no=row['voucher_no'])
			dn_doc.make_gl_entries(repost_future_gle=False, from_repost=False)
		if row['voucher_type'] == "Purchase Receipt":
			pr_doc = frappe.get_doc("Purchase Receipt",row['voucher_no'])
			print(pr_doc.name)
			delete_gl_entries(voucher_type=row['voucher_type'],voucher_no=row['voucher_no'])
			pr_doc.make_gl_entries()
			
def get_data():
	sle_data = get_sle_value()
	gl_data = get_gl_value()
	data=[]
	for sl in sle_data:

		try:
			gl_value = gl_data[sl.voucher_no]['gl_value']
			del gl_data[sl.voucher_no]
		except KeyError:
			gl_value = 0.0		
		sl['gl_value'] = gl_value or 0.0
		sl['value_diff'] = round((flt(sl['gl_value']) - flt(sl['sle_value'])),0)
		if sl['value_diff']:
			data.append(sl)
	
	return data

def get_sle_value():
	return frappe.db.sql("""
			select
				sum(sle.stock_value_difference) as sle_value, sle.posting_date, sle.voucher_type, sle.voucher_no, sle.company
			from
				`tabStock Ledger Entry` sle
			where sle.docstatus < 2 and sle.stock_value_difference<>0
			group by sle.voucher_no
			order by sle.posting_date""", as_dict=1)


def get_gl_value():
	gl_data = frappe.db.sql("""
			select
				sum(gl.debit_in_account_currency - gl.credit_in_account_currency) as gl_value, gl.voucher_no
			from
				`tabGL Entry` gl JOIN `tabAccount` ac ON gl.account = ac.name
			where gl.docstatus < 2 and ac.account_type = "Stock"
			group by gl.voucher_no
			order by gl.posting_date""", as_dict=1)

	return get_gl_map(gl_data)

def get_gl_map(gl_data):
	gl_map = {}
	for d in gl_data:
		gl_map.setdefault(d.voucher_no, frappe._dict({
				"gl_value": 0.0
			}))
		gl_dict = gl_map[d.voucher_no]
		gl_dict["gl_value"] = flt(d.gl_value)
	return gl_map
