# Copyright (c) 2013, Finbyz and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import collections, functools, operator
from past.builtins import cmp
from frappe import _
from frappe.utils import flt
from finbyzerp.finbyzerp.report.item_wise_purchase_register import _execute as purchase_execute
from finbyzerp.finbyzerp.report.item_wise_sales_register import _execute as sales_execute

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters) 
	data = get_data(filters)
	return columns, data

def get_data(filters):
	item_group = get_item_group(filters)

	if not item_group:
		return None
	item_group = filter_item_group(filters, item_group)

	out = prepare_data(filters, item_group)
	data = get_final_out(filters, out)

	return data

def get_group_map(out):
	sorted_out = sorted(out, key = lambda i: (i['indent'],i['parent_item_group']),reverse=True)
	item_group_map = {}		

	for row in sorted_out:
		if row.is_group ==1 and item_group_map.get(row.item_group):
			row.net_amount = item_group_map.get(row.item_group).net_amount
			row.tax_amount = item_group_map.get(row.item_group).tax_amount
			row.total_amount = item_group_map.get(row.item_group).total_amount
		if row.parent_item_group:
			item_group_map.setdefault(row.parent_item_group, frappe._dict({
					"net_amount": 0.0,"tax_amount": 0.0,"total_amount":0.0
				}))
			item_group_dict = item_group_map[row.parent_item_group]
			item_group_dict.net_amount += flt(row.net_amount)
			item_group_dict.tax_amount += flt(row.tax_amount)
			item_group_dict.total_amount += flt(row.total_amount)
	
	return item_group_map

def get_final_out(filters, out):
	data = []
	item_group_map = get_group_map(out)
	for row in out:
		if row.is_group and item_group_map.get(row.item_group):
			row.net_amount = item_group_map.get(row.item_group).net_amount
			row.tax_amount = item_group_map.get(row.item_group).tax_amount
			row.total_amount = item_group_map.get(row.item_group).total_amount
		data.append(row)

	return data
		

def get_item_group(filters):
	item_group = frappe.db.sql("""
		select 
			name, parent_item_group, 1 as is_group
		from
			`tabItem Group`
		order by lft""", as_dict=True)

	item = frappe.db.sql("""
		select 
			name, item_code, item_name, item_group as parent_item_group, 0 as is_group
		from
			`tabItem`
		""", as_dict=True)
	
	item_map, item_tax_map = get_item_map(filters)
	item.append(frappe._dict({"name":"Opening Invoice Item","item_code":"Opening Invoice Item","item_name":"Opening Invoice Item",
			"parent_item_group":"All Item Groups","is_group":0}))
	nt = 0
	for data in item:
		data.net_amount = item_map.get(data.name) or (0)
		data.tax_amount = item_tax_map.get(data.name) or (0)
		data.total_amount = data.net_amount + data.tax_amount
		nt += data.net_amount
	return (item_group + item)
	

def get_item_map(filters):
	gst_accounts = frappe.get_doc("GST Account",{"parent":"GST Settings","company":filters.company,"is_reverse_charge_account":0})
	gst_accounts_reverse = frappe.get_doc("GST Account",{"parent":"GST Settings","company":filters.company,"is_reverse_charge_account":1})
	accounts = frappe._dict({"cgst_account":gst_accounts.cgst_account,"sgst_account":gst_accounts.sgst_account,
							"igst_account":gst_accounts.igst_account,"cess_account":gst_accounts.cess_account,
							"tcs_account":gst_accounts.tcs_account,"export_reverse_charge_account":gst_accounts.export_reverse_charge_account})

	reverse_accounts = frappe._dict({"cgst_account":gst_accounts_reverse.cgst_account,"sgst_account":gst_accounts_reverse.sgst_account,
							"igst_account":gst_accounts_reverse.igst_account,"cess_account":gst_accounts_reverse.cess_account,
							"tcs_account":gst_accounts_reverse.tcs_account,"export_reverse_charge_account":gst_accounts_reverse.export_reverse_charge_account})

	purchase_tax_amount_data = purchase_execute(filters)
	sales_tax_amount_data = sales_execute(filters)
		
	# data = frappe.db.sql("""
	# 	select pii.item_code, pii.net_amount as net_amount 
	# 	from `tabPurchase Invoice Item` as pii
	# 	JOIN `tabPurchase Invoice` as pi on pi.name = pii.parent
	# 	where pi.company = '{}' and pi.docstatus = 1 and (pii.item_code is not null or pii.item_code != '') and (pii.item_group is not null or pii.item_group != '')
	# """.format(filters.company), as_dict = 1)

	item_map = {}
	item_tax_map = {}
	if filters.get('purchase') and not filters.get('sales'):
		item_map, item_tax_map = get_purchase_data(filters,accounts,reverse_accounts,item_map,item_tax_map,purchase_tax_amount_data)
	elif filters.get('sales') and not filters.get('purchase'):
		item_map, item_tax_map = get_sales_data(filters,accounts,reverse_accounts,item_map,item_tax_map,sales_tax_amount_data)
	else:
		item_map, item_tax_map = get_purchase_data(filters,accounts,reverse_accounts,item_map,item_tax_map,purchase_tax_amount_data)
		item_map, item_tax_map = get_sales_data(filters,accounts,reverse_accounts,item_map,item_tax_map,sales_tax_amount_data)

	return item_map, item_tax_map

def get_purchase_data(filters,accounts,reverse_accounts,item_map,item_tax_map,purchase_tax_amount_data):
	for tax in purchase_tax_amount_data[1]:
		if tax['item_code'] in item_tax_map:
			item_tax_map[tax['item_code']] += ((flt(tax.get(frappe.scrub(accounts.get("cgst_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(accounts.get("sgst_account") or "") + "_amount")) or 0)
									+ (flt(tax.get(frappe.scrub(accounts.get("igst_account") or "") + "_amount"))or 0) + (flt(tax.get(frappe.scrub(accounts.get("cess_account") or "") + "_amount")) or 0) 
									+ (flt(tax.get(frappe.scrub(accounts.get("tcs_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(accounts.get("export_reverse_charge_account") or "") + "_amount")) or 0)
									+ (flt(tax.get(frappe.scrub(reverse_accounts.get("cgst_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(reverse_accounts.get("sgst_account") or "") + "_amount")) or 0)
									+ (flt(tax.get(frappe.scrub(reverse_accounts.get("igst_account") or "") + "_amount"))or 0) + (flt(tax.get(frappe.scrub(reverse_accounts.get("cess_account") or "") + "_amount")) or 0) 
									+ (flt(tax.get(frappe.scrub(reverse_accounts.get("tcs_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(reverse_accounts.get("export_reverse_charge_account") or "") + "_amount")) or 0))

		else:
			item_tax_map[tax['item_code']] = ((flt(tax.get(frappe.scrub(accounts.get("cgst_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(accounts.get("sgst_account") or "") + "_amount")) or 0)
									+ (flt(tax.get(frappe.scrub(accounts.get("igst_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(accounts.get("cess_account") or "") + "_amount")) or 0) 
									+ (flt(tax.get(frappe.scrub(accounts.get("tcs_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(accounts.get("export_reverse_charge_account") or "") + "_amount")) or 0)
									+ (flt(tax.get(frappe.scrub(reverse_accounts.get("cgst_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(reverse_accounts.get("sgst_account") or "") + "_amount")) or 0)
									+ (flt(tax.get(frappe.scrub(reverse_accounts.get("igst_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(reverse_accounts.get("cess_account") or "") + "_amount")) or 0) 
									+ (flt(tax.get(frappe.scrub(reverse_accounts.get("tcs_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(reverse_accounts.get("export_reverse_charge_account") or "") + "_amount")) or 0))

		if tax['item_code'] in item_map:
			item_map[tax['item_code']] += tax.get('amount') or 0
		else:
			item_map[tax['item_code']] = tax.get('amount') or 0

		if tax['item_name'] == "Opening Invoice Item":
			if tax['item_name'] in item_map:
				item_map[tax['item_name']] += tax.get('amount') or 0
			else:
				item_map[tax['item_name']] = tax.get('amount') or 0

	return item_map, item_tax_map

def get_sales_data(filters,accounts,reverse_accounts,item_map,item_tax_map,sales_tax_amount_data):
	for tax in sales_tax_amount_data[1]:
		if tax['item_code'] in item_tax_map:
			item_tax_map[tax['item_code']] += ((flt(tax.get(frappe.scrub(accounts.get("cgst_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(accounts.get("sgst_account") or "") + "_amount")) or 0)
									+ (flt(tax.get(frappe.scrub(accounts.get("igst_account") or "") + "_amount"))or 0) + (flt(tax.get(frappe.scrub(accounts.get("cess_account") or "") + "_amount")) or 0) 
									+ (flt(tax.get(frappe.scrub(accounts.get("tcs_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(accounts.get("export_reverse_charge_account") or "") + "_amount")) or 0))
		else:
			item_tax_map[tax['item_code']] = ((flt(tax.get(frappe.scrub(accounts.get("cgst_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(accounts.get("sgst_account") or "") + "_amount")) or 0)
									+ (flt(tax.get(frappe.scrub(accounts.get("igst_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(accounts.get("cess_account") or "") + "_amount")) or 0) 
									+ (flt(tax.get(frappe.scrub(accounts.get("tcs_account") or "") + "_amount")) or 0) + (flt(tax.get(frappe.scrub(accounts.get("export_reverse_charge_account") or "") + "_amount")) or 0))

		if tax['item_code'] in item_map:
			item_map[tax['item_code']] += tax.get('amount') or 0
		else:
			item_map[tax['item_code']] = tax.get('amount') or 0

		if tax['item_name'] == "Opening Invoice Item":
			if tax['item_name'] in item_map:
				item_map[tax['item_name']] += tax.get('amount') or 0
			else:
				item_map[tax['item_name']] = tax.get('amount') or 0

	return item_map, item_tax_map

def filter_item_group(filters,item_group, depth=10):
	parent_children_map = {}
	item_group_by_name = {}
	
	for d in item_group:
		item_group_by_name[d.name] = d
		parent_children_map.setdefault(d.parent_item_group or None, []).append(d)
	
	non_unique_filtered_item_group = []
	filtered_item_group = []

	def add_to_list(parent, level):

		if level < depth:
			children = parent_children_map.get(parent) or []
			sort_item_group(children, is_root=True if parent==None else False)

			for child in children:
				child.indent = level
				if child.get('name') not in non_unique_filtered_item_group:
					filtered_item_group.append(child)
					non_unique_filtered_item_group.append(child.name)
				add_to_list(child.name, level + 1)

	add_to_list(None, 0)

	return filtered_item_group

def sort_item_group(item_group, is_root=False, key="name"):

	def compare_item_groups(a, b):
		return cmp(a[key], b[key]) or 1

	item_group.sort(key = functools.cmp_to_key(compare_item_groups))

def prepare_data(filters,item_group):
	data = []

	for d in item_group:
		# add to output
		row = frappe._dict({
			"item_code": _(d.item_code or ''),
			"item_group": _(d.item_name or d.name),
			"parent_item_group": _(d.parent_item_group),
			"indent": flt(d.indent),
			"net_amount": flt(d.net_amount),
			"tax_amount": flt(d.tax_amount),
			"total_amount": flt(d.total_amount),
			"is_group": d.is_group
		})
		data.append(row)
	return data

def get_columns(filters):
	return [
		{
			"fieldname": "item_group",
			"label": ("Item Group"),
			"fieldtype": "Data",
			"options": "Item Group",
			"width": 350
		},
		{
			"fieldname": "net_amount",
			"label": ("Net Amount"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "tax_amount",
			"label": ("Tax Amount"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "total_amount",
			"label": "Total Amount",
			"fieldtype": "Currency",
			"width": 150
		},
	]