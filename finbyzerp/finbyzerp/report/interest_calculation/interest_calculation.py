# Copyright (c) 2022, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from finbyzerp.finbyzerp.doc_events.account import get_gl_data
from erpnext.accounts.utils import get_children


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_data(filters):
	account_list=[row.value for row in get_children("Account",filters.get('account'),filters.get('company'))]
	report_data=[]
	for each_account in account_list:

		report_data.append(get_interest_amount(filters,each_account))
	
	return report_data

def get_columns(filters):
	return [
		{"fieldname": "account", "label": ("Account"), "fieldtype": "Data", "width": 300},
		{"fieldname": "opening_bal", "label": ("Opening Balance"), "fieldtype": "Float", "width": 200},
		{"fieldname": "interest_days", "label": ("Days"), "fieldtype": "Data", "width": 100},	
		{"fieldname": "interest_rate", "label": ("Interest Rate"), "fieldtype": "Float", "width": 200},
		{"fieldname": "interest_amount", "label": ("Interest Amount"), "fieldtype": "Float", "width": 200},
		{"fieldname": "closing_bal", "label": ("Closing Balance"), "fieldtype": "Float", "width": 200},
	]

def get_interest_amount(filters,account):
	interest_rate=frappe.db.get_value("Account",account,'interest_rate') or frappe.db.get_value("Company",filters.get('company'),'default_interest_rate') or 0
	gl_data=get_gl_data(
				from_date=filters.get('from_date'),
				to_date=filters.get('to_date'),
				company=filters.get('company'),
				account=account,
				get_opening_closing_data=1
			)
	closing_details = frappe.db.sql(f"""
			SELECT
				IFNULL(SUM(debit - credit), 0) as closing_balance
			FROM
				`tabGL Entry`
			WHERE
				posting_date <= '{filters.get('to_date')}' and account ='{account}' and is_cancelled=0
		""")[0][0] or 0
	data={'interest_amount':0.0,'interest_days':0,"account":account,'opening_bal':0,'interest_rate':interest_rate,"closing_bal":closing_details}
	if gl_data:
		data['opening_bal'] = gl_data[0]['balance']
	for each in gl_data:
		data['interest_amount']+=(each.get('balance') * each.get("days") * interest_rate / (365 * 100))
		data['interest_days']+= each.get("days")
	
	return data