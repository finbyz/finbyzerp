
# Copyright (c) 2013, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries
# import frappe

# Before executing patch comment this: sle = self.update_stock_ledger_entries(sle) and write pass there in line_no = 91 in
		#erpnext/erpnext/controllers/stock_controller.py 

#Patch Start: run for all the item with all warehouse
def execute_update_entries_after():
	item_list = frappe.db.get_all("Item",fields=["name as item_code"])
	warehouse = frappe.db.get_all("Warehouse",fields=["name as warehouse"])

	from erpnext.stock.stock_ledger import update_entries_after

	for w in warehouse:
		for item in item_list:
			print(item.item_code)
			args = {
				"item_code": item.item_code,
				"warehouse": w.warehouse,
				"posting_date": "2015-01-01",
				"posting_time": "01:01:00"
			}
			update_entries_after(args)

def check_bin_multiple_items_with_warehouse():
	bin_list = frappe.db.get_list("Bin",{},['*'])
	bin_dict = {}
	duplicate = []
	total_stock_value = 0
	for b in bin_list:
		if (b.item_code,b.warehouse) not in bin_dict:
			bin_dict[(b.item_code,b.warehouse)] = b
		else:
			duplicate.append(frappe._dict({"item_code":b.item_code,"warehouse":b.warehouse}))

		stock_value_diff_query = frappe.db.sql("""select sum(stock_value_difference)
			from `tabStock Ledger Entry`
			where item_code = '{}' and warehouse = '{}' and is_cancelled = 0
			group by item_code""".format(b.item_code,b.warehouse))
			
		if stock_value_diff_query:
			stock_value_diff = stock_value_diff_query[0][0]
		else:
			stock_value_diff = 0.0

		# stock_value_query = frappe.db.sql("""select stock_value,name
		# from `tabStock Ledger Entry`
		# where item_code = '{}' and warehouse = '{}' and is_cancelled = 0
		# order by timestamp(posting_date, posting_time) DESC, creation DESC limit 1""".format(b.item_code,b.warehouse))

		# if stock_value_query:
		# 	stock_value = stock_value_query[0][0]
		# else:
		# 	stock_value = 0

		# if stock_value != stock_value_diff:
		# 	print(b.name,b.item_code,b.warehouse,stock_value_query[0][1])

		total_stock_value += stock_value_diff
		if stock_value_diff != b.stock_value:
			print(b.name, b.item_code)
			# frappe.db.set_value("Bin",b.name,"stock_value",stock_value_diff)
		
	print(total_stock_value)

# Patch End
def patch():
	data = get_data()
	print(data)
	for row in data:
		if row['voucher_type'] in ["Stock Entry","Stock Reconciliation"]:
			se_doc = frappe.get_doc(row['voucher_type'],row['voucher_no'])
			print(se_doc.name)
			# delete_gl_entries(voucher_type=row['voucher_type'],voucher_no=row['voucher_no'])
			make_reverse_gl_entries(voucher_type=row['voucher_type'],voucher_no=row['voucher_no'])
			se_doc.make_gl_entries(from_repost=False)
		if row['voucher_type'] == "Payment Entry":
			pe_doc = frappe.get_doc("Payment Entry",row['voucher_no'])
			print(pe_doc.name)
			pe_doc.make_gl_entries(cancel=1)
			pe_doc.make_gl_entries(cancel=0)
		if row['voucher_type'] == "Delivery Note":
			dn_doc = frappe.get_doc("Delivery Note",row['voucher_no'])
			print(dn_doc.name)
			# delete_gl_entries(voucher_type=row['voucher_type'],voucher_no=row['voucher_no'])
			make_reverse_gl_entries(voucher_type=row['voucher_type'],voucher_no=row['voucher_no'])
			dn_doc.make_gl_entries(from_repost=False)
		if row['voucher_type'] in ["Purchase Receipt","Purchase Invoice"]:
			pr_doc = frappe.get_doc(row['voucher_type'],row['voucher_no'])
			print(pr_doc.name)
			# delete_gl_entries(voucher_type=row['voucher_type'],voucher_no=row['voucher_no'])
			make_reverse_gl_entries(voucher_type=row['voucher_type'],voucher_no=row['voucher_no'])
			pr_doc.make_gl_entries()
		if row['voucher_type'] in ["Sales Invoice"]:
			si_doc = frappe.get_doc(row['voucher_type'],row['voucher_no'])
			print(si_doc.name)
			# delete_gl_entries(voucher_type=row['voucher_type'],voucher_no=row['voucher_no'])
			make_reverse_gl_entries(voucher_type=row['voucher_type'],voucher_no=row['voucher_no'])
			si_doc.make_gl_entries()

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
			where sle.docstatus < 2 and sle.is_cancelled = 0 and sle.stock_value_difference<>0
			group by sle.voucher_no
			order by sle.posting_date""" , as_dict=1)


def get_gl_value():
	gl_data = frappe.db.sql("""
			select
				sum(gl.debit_in_account_currency - gl.credit_in_account_currency) as gl_value, gl.voucher_no
			from
				`tabGL Entry` gl JOIN `tabAccount` ac ON gl.account = ac.name
			where gl.docstatus < 2 and gl.is_cancelled = 0 and ac.account_type in ("Stock","Capital Work in Progress","Fixed Asset")
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
