# Copyright (c) 2013, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
# import frappe

def execute(filters):
	from_date = filters.get('from_date')
	to_date = filters.get('to_date')
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	columns = [
		{"label": _("Voucher No"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 140},
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 80},
		{"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Link", "options": "Doctype", "width": 120},
		{"label": _("SLE Value"), "fieldname": "sle_value", "fieldtype": "Currency", "width": 100},
		{"label": _("GL Value"), "fieldname": "gl_value", "fieldtype": "Currency", "width": 100},
		{"label": _("Value Diff"), "fieldname": "value_diff", "fieldtype": "Currency", "width": 100},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 200}
	]
	return columns



def get_data(filters):
	sle_data = get_sle_value(filters)
	gl_data = get_gl_value(filters)
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



	


def get_sle_value(filters):

	conditions = ""	
	if filters.get("from_date"):
		conditions += " and sle.posting_date >= %s" % frappe.db.escape(filters.get("from_date"))

	if filters.get("to_date"):
		conditions += " and sle.posting_date <= %s" % frappe.db.escape(filters.get("to_date"))

	if filters.get("company"):
		conditions += " and sle.company = %s" % frappe.db.escape(filters.get("company"))

	return frappe.db.sql("""
			select
				sum(sle.stock_value_difference) as sle_value, sle.posting_date, sle.voucher_type, sle.voucher_no, sle.company
			from
				`tabStock Ledger Entry` sle
			where sle.docstatus < 2 and sle.is_cancelled = 0 and sle.stock_value_difference<>0%s
			group by sle.voucher_no
			order by sle.posting_date""" %
			(conditions), as_dict=1)


def get_gl_value(filters):
	conditions = ""	
	if filters.get("from_date"):
		conditions += " and gl.posting_date >= %s" % frappe.db.escape(filters.get("from_date"))

	if filters.get("to_date"):
		conditions += " and gl.posting_date <= %s" % frappe.db.escape(filters.get("to_date"))

	if filters.get("company"):
		conditions += " and gl.company = %s" % frappe.db.escape(filters.get("company"))

	gl_data = frappe.db.sql("""
			select
				sum(gl.debit_in_account_currency - gl.credit_in_account_currency) as gl_value, gl.voucher_no
			from
				`tabGL Entry` gl JOIN `tabAccount` ac ON gl.account = ac.name
			where gl.docstatus < 2 and gl.is_cancelled = 0 and ac.account_type in ("Stock","Capital Work in Progress","Fixed Asset")%s
			group by gl.voucher_no
			order by gl.posting_date""" %
			(conditions), as_dict=1)

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