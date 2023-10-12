# Copyright (c) 2023, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
import re

def execute(filters=None):
	if filters.get("from_date") and filters.get("to_date"):
		if filters.get("from_date") > filters.get("to_date"):
			frappe.throw(_("From Date cannot be less than To Date"))

	columns, data = get_data(filters)
	return columns, data


def get_data(filters):
	conditions = ""

	if filters.get("item_code"):
		conditions += f"and qi.item_code = {frappe.db.escape(filters.get('item_code'))}"
	
	if filters.get("item_group"):
		conditions += f"and qi.item_group = {frappe.db.escape(filters.get('item_group'))}"
	
	if filters.get("status"):
		conditions += f"and qi.status = {frappe.db.escape(filters.get('status'))}"
	
	if filters.get("docstatus"):
		if filters.get("docstatus") == "Draft":
			conditions += " and qi.docstatus = 0"
		if filters.get("docstatus") == "Submitted":
			conditions += " and qi.docstatus = 1"

	quality_inspection_data = frappe.db.sql(f"""
		SELECT 
			qi.report_date, 
			qi.name,
			qi.lot_number,
			qi.type_of_quality,
			qi.type_of_report,
			qi.shade,
			qi.item_code,
			qi.item_group,
			qi.status,
			qi.reference_type,
			qi.reference_name,
			qir.specification, qir.reading_value
		FROM 
			`tabQuality Inspection Reading` as qir
		LEFT JOIN 
			`tabQuality Inspection` as qi ON qir.parent = qi.name
		WHERE
			qi.report_date between %s AND %s
			{conditions}
	""", (filters['from_date'], filters['to_date']), as_dict=True)


	data = []
	unique_data = {}

	columns = [
			{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "options": "Quality Inspection", "width": 150},
			{"label": _("Report Date"), "fieldname": "report_date", "fieldtype": "Date", "width": 100},
			{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
			{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link","options":"Item", "width": 150},
			{"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link","options":"Item Group", "width": 120},
			{"label": _("Lot No"), "fieldname": "lot_no", "fieldtype": "Data", "width": 100},
			{"label": _("Type Of Quality"), "fieldname": "type_of_quality", "fieldtype": "Data", "width": 100},
			{"label": _("Type Of Report"), "fieldname": "type_of_report", "fieldtype": "Data", "width": 100},
			{"label": _("Shade "), "fieldname": "shade", "fieldtype": "Data", "width": 100},
			{"label": _("Reference Type"), "fieldname": "ref_type", "fieldtype": "Data", "width": 150},
			{"label": _("Reference Name"), "fieldname": "ref_name", "fieldtype": "Data","width": 150},\
		]

	unique_specification = []
	for row in quality_inspection_data:
		if row.specification not in unique_specification:
			columns.append({"label": _(f"{row.specification}"), "fieldname": f"{row.specification}", "fieldtype": "Data", "width": 80})
			unique_specification.append(row.specification)
		
		if unique_data.get(row.name):
			unique_data[row.name][row.specification] = row.reading_value
		else:
			unique_data.update({row.name : {}})
			unique_data[row.name].update({
				"name": row.name,
				"report_date": row.report_date, "lot_no": row.lot_number, "item_code": row.item_code, "item_group": row.item_group, 
				"status": row.status,"type_of_quality": row.type_of_quality, "type_of_report": row.type_of_report, "shade": row.shade, "ref_type": row.reference_type, "ref_name": row.reference_name, row.specification : row.reading_value
			})

	data = []
	for row in unique_data:
		data.append(unique_data[row])

	return columns, data