# Copyright (c) 2013, Finbyz and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import functools
from past.builtins import cmp
from frappe import _
from frappe.utils import flt
# import frappe

def execute(filters=None):
	columns, data = [], []
	columns = [
		{
			"fieldname": "item_group",
			"label": ("Item Group"),
			"fieldtype": "Data",
			"options": "Item Group",
			"width": 350
		},
		{
			"fieldname": "balance_qty",
			"label": ("Balance Qty"),
			"fieldtype": "Float",
			"width": 150
		},
		{
			"fieldname": "valuation",
			"label": ("Avg Valuation"),
			"fieldtype": "Float",
			"width": 150
		},
		{
			"fieldname": "balance_value",
			"label": ("Balance Value"),
			"fieldtype": "Float",
			"width": 150
		},
		{
			"fieldname": "view_sle",
			"label": "Stock Ledger",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "view_stock_balance",
			"label": "Stock Balance",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "view_monthly_stock_balance",
			"label": "Stock Balance",
			"fieldtype": "Data",
			"width": 200
		},
	]
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
			row.balance_qty = item_group_map.get(row.item_group).balance_qty
			row.balance_value = item_group_map.get(row.item_group).balance_value
		if row.parent_item_group:
			item_group_map.setdefault(row.parent_item_group, frappe._dict({
					"balance_qty": 0.0,
					"balance_value": 0.0
				}))
			item_group_dict = item_group_map[row.parent_item_group]
			item_group_dict.balance_qty += flt(row.balance_qty)
			item_group_dict.balance_value += flt(row.balance_value)
	return item_group_map

def get_final_out (filters, out):
	data = []
	item_group_map = get_group_map(out)
	for row in out:
		if row.is_group and item_group_map.get(row.item_group):
			row.balance_qty = item_group_map.get(row.item_group).balance_qty
			row.balance_value = item_group_map.get(row.item_group).balance_value
		
		if filters.get('show_0_qty_inventory'):
			if row.balance_qty > 0:
				row.valuation = flt(row.balance_value)/flt(row.balance_qty)
			else:
				row.valuation = 0
			data.append(row)
		else:
			if row.balance_qty > 0:
				row.valuation = flt(row.balance_value)/flt(row.balance_qty)
				data.append(row)

		if row.is_group:
			row.view_sle = f"""
				<button class="btn btn-primary btn-sm primary-action" 
					type='button' company='{filters.company}' warehouse='{filters.get("warehouse") or ''}' item-group='{row.item_group}'
					onClick='route_to_sle(this.getAttribute("company"),this.getAttribute("warehouse"),this.getAttribute("item-group"))'>View Stock Ledger</button>"""

			row.view_stock_balance = f"""<button class="btn btn-primary btn-sm primary-action" 
					type='button' company='{filters.company}' warehouse='{filters.get("warehouse") or ''}' item-group='{row.item_group}'
					onClick='route_to_stock_balance(this.getAttribute("company"),this.getAttribute("warehouse"),this.getAttribute("item-group"))'>View Stock Balance</button>"""

			row.view_monthly_stock_balance = f"""<button class="btn btn-primary btn-sm primary-action" 
					type='button' company='{filters.company}' item-group='{row.item_group}'
					onClick='route_to_monthly_stock_balance(this.getAttribute("company"),this.getAttribute("item-group"))'>View Monthly Stock Balance</button>"""

		if not row.is_group:
			row.view_sle = f"""
				<button class="btn btn-primary btn-sm primary-action"
					type='button' company='{filters.company}' warehouse='{filters.get("warehouse") or ''}' item-name='{row.item_code}'
					onClick='route_to_sle_item(this.getAttribute("company"),this.getAttribute("warehouse"),this.getAttribute("item-name"))'>View Stock Ledger</button>"""

			row.view_stock_balance = f"""
				<button class="btn btn-primary btn-sm primary-action" 
					type='button' company='{filters.company}' warehouse='{filters.get("warehouse") or ''}' item-name='{row.item_code}'
					onClick='route_to_stock_balance_item(this.getAttribute("company"),this.getAttribute("warehouse"),this.getAttribute("item-name"))'>View Stock Balance</button>"""

			row.view_monthly_stock_balance = f"""
				<button class="btn btn-primary btn-sm primary-action" 
					type='button' company='{filters.company}' item-name='{row.item_code}'
					onClick='route_to_monthly_stock_balance_item(this.getAttribute("company"),this.getAttribute("item-name"))'>View Monthly Stock Balance</button>"""

	return data
		

def get_item_group(filters):
	item_group = frappe.db.sql("""
		select 
			name, parent_item_group, 1 as is_group
		from
			`tabItem Group`
		order by lft""", as_dict=True)
	# cond = ''
	# if filters.get('authorized') and not filters.get('unauthorized'):
	# 	cond += " and authority = 'Authorized'"
	# if filters.get('unauthorized') and not filters.get('authorized'):
	# 	cond += " and authority = 'Unauthorized'"

	item = frappe.db.sql("""
		select 
			name, item_code, item_name, item_group as parent_item_group, 0 as is_group
		from
			`tabItem`
		where
			ifnull(disabled,0) = 0	
		""", as_dict=True)
	
	item_map = get_item_map(filters)
	for data in item:
		data.balance_qty, data.balance_value = item_map.get(data.name) or (0, 0)

	return (item_group + item)
	

def get_item_map(filters):
	filter_warehouse = ''

	if filters.get('warehouse'):
		filter_warehouse = " and b.warehouse = '{}'".format(filters.warehouse)

	data = frappe.db.sql(f"""
		select b.item_code, sum(actual_qty) as qty, sum(stock_value) as value
		from `tabBin` as b JOIN `tabWarehouse` as w on w.name = b.warehouse
		where w.company = '{filters.company}'{filter_warehouse}
		group by b.item_code
	""", as_dict = 1)

	item_map = {}

	for row in data:
		item_map[row.item_code] = [row.qty, row.value]

	return item_map

def filter_item_group(filters,item_group, depth=10):
	parent_children_map = {}
	item_group_by_name = {}
	
	for d in item_group:
		item_group_by_name[d.name] = d
		parent_children_map.setdefault(d.parent_item_group or None, []).append(d)
	
	non_unique_filtered_item_group = []
	non_unique_filtered_item_name = []
	filtered_item_group = []

	def add_to_list(parent, level):

		if level < depth:
			children = parent_children_map.get(parent) or []
			sort_item_group(children, is_root=True if parent==None else False)
			for child in children:
				child.indent = level
				if child.get('name') not in non_unique_filtered_item_group and child.get('is_group') == 1:
					filtered_item_group.append(child)
					non_unique_filtered_item_group.append(child.name)
				elif child.get('name') not in non_unique_filtered_item_name and child.get('is_group') == 0:
					filtered_item_group.append(child)
					non_unique_filtered_item_name.append(child.name)
				
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
			"balance_qty": flt(d.balance_qty),
			"balance_value": flt(d.balance_value),
			"is_group": d.is_group
		})
		data.append(row)
	return data