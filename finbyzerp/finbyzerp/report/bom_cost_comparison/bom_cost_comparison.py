# Copyright (c) 2013, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from asyncio import constants
from typing import final
import frappe
from frappe import _
# import frappe
import re
from frappe.utils.data import get_link_to_form
from frappe.share import add

# function to clean string for names in coloumn


def clean_string(string):
	if string:
		string = string.replace(" ", "_")
		string = string.lower()
		string = re.sub('[^A-Za-z0-9_]+', '', string)
	return string


def execute(filters=None):
	if not filters:
		filters = {}
	from_date = filters.get("from_date", None)
	to_date = filters.get("to_date", None)

	if from_date and to_date:
		if from_date > to_date:
			frappe.throw(_("From Date cannot be less than To Date"))

	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data


def get_columns(filters):
	columns = [
		{"label": _("Raw Material"), "fieldname": "raw_material",
		 "fieldtype": "Link", "options": "Item", "width": 150}
	]

	# append dynamic columns of BOM
	data = column_query(filters)

	for d in data:
		x = {"label": _("{}".format(d[0])), "fieldname": d[0],
			 "fieldtype": "Data", "width": 150,"align": 'right'}
		columns.append(x)

	columns.append({"label": _("Rate"), "fieldname": "rate",
				   "fieldtype": "Currency", "width": 150})
	return columns


def column_query(filters):
	conditions = ''
	if not filters.get('bom'):
		conditions += f"and item = '{filters.get('item')}' and creation between '{filters.get('from_date')}' and '{filters.get('to_date')}'"
	else:
		conditions += " and name in {} ".format(
			"(" + ", ".join([f'"{l}"' for l in filters.get("bom")]) + ")")
	# Getting dynamic column name
	column = frappe.db.sql(f"""
	SELECT 
		name from `tabBOM`
	WHERE
		docstatus = 1
		{conditions}
	""")
	return column


def get_data(filters):
	# adding where condition according to filters
	condition = ''
	if not filters.get('bom'):
		condition += f"and bom.item = '{filters.get('item')}' and bom.creation between '{filters.get('from_date')}' and '{filters.get('to_date')}'"
	else:
		condition += " and bom.name in {} ".format(
			"(" + ", ".join([f'"{l}"' for l in filters.get("bom")]) + ")")
	
	# sql query to get data for column
	data = frappe.db.sql(f"""
		SELECT 
			bom_item.item_code, bom_item.qty, bom_item.rate as rate,
			bom.name as bom
		FROM
			`tabBOM Item` as bom_item
			LEFT JOIN `tabBOM` as bom ON bom_item.parent = bom.name
		WHERE bom.docstatus = 1 {condition}
		""", as_dict=1)

	item_code_dict = {}
	bom_dict = {}
	for row in data:
		bom_dict[row.bom] = get_link_to_form("BOM", row.bom)
		if item_code_dict.get(row.item_code):
			item_code_dict[row.item_code].update({row.bom: [row.qty, row.rate]})
		else:
			item_code_dict[row.item_code] = {row.bom: [row.qty, row.rate]}

	final_data_list = []
	final_data_list.append(bom_dict)
	for item in item_code_dict:
		final_data = {}

		for row in data:
			if item_code_dict[item].get(row.bom):
				final_data.update(
					{"raw_material": item, row.bom: round(item_code_dict[item][row.bom][0], 2), "rate" : item_code_dict[item][row.bom][1]})
			else:
				final_data.update({"raw_material": item, row.bom: 0})

		if final_data:
			final_data_list.append(final_data)

	additional_data = frappe.db.sql(f"""
		SELECT
			name, per_unit_rmc as raw_material_cost, per_unit_operational_cost, total_cost, quantity
		FROM
			`tabBOM`
		WHERE docstatus = 1 and item = '{filters.get('item')}' and creation between '{filters.get('from_date')}' and '{filters.get('to_date')}'
	""", as_dict=1)

	material_dict = {"raw_material": "Raw Material Cost"}
	operational_dict = {"raw_material": "Per Unit Operational_cost"}
	total_cost_dict = {"raw_material": "Total Cost"}

	for bom in additional_data:
		material_dict.update({bom.name:  round(bom.raw_material_cost, 2)})
		operational_dict.update({bom.name:  round(bom.per_unit_operational_cost, 2)})
		total_cost_dict.update({bom.name: round((bom.total_cost / bom.quantity), 2)})

	final_data_list.append(material_dict)
	final_data_list.append(operational_dict)
	final_data_list.append(total_cost_dict)

	return final_data_list
	