# Copyright (c) 2023, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.financial_statements import get_columns, get_data, get_period_list


def execute(filters=None):
	columns, data = [], []

	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def get_columns(filters):
	return [
		{
			"label": _("Ratio"),
			"fieldname": "ratio",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Numerator / Denominator"),
			"fieldname": "numerator_denominator",
			"fieldtype": "Data",
			"width": 350,
		},
		{
			"label": _(f"{filters.get('start_year')}"),
			"fieldname": f"{filters.get('start_year')}",
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"label": _(f"{filters.get('end_year')}"),
			"fieldname": f"{filters.get('end_year')}",
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"label": _("Variance"),
			"fieldname": "variance",
			"fieldtype": "Percent",
			"width": 150,
		},
	]

def get_data(filters):
	data = []
	account_dict = {}
	account_list = []
	cols = frappe.db.get_all("DocField", {'parent': "Financial Ratio Analysis"}, ['fieldname', 'fieldtype'], order_by="idx")
	for row in cols:
		if row.get('fieldname') != "company":
			if row.get('fieldtype') == "Section Break":
				key = row['fieldname']
				account_dict[key] = []
			elif row.get('fieldtype') != "Column Break":
				if row['fieldname'] not in account_list:
					account_list.append(row['fieldname'])
				account_dict[key].append(row.fieldname)

	start_year_date = frappe.db.get_value("Fiscal Year", filters.get('start_year'), "year_end_date")
	end_year_date = frappe.db.get_value("Fiscal Year", filters.get('end_year'), "year_end_date")

	closing_dict = {}

	for row in account_list:
		account = frappe.db.sql(f"""
				SELECT {row} 
				FROM `tabFinancial Ratio Analysis`
			""")
		
		if account:

			closing_dict[row] = {'account' : account[0][0], filters.get('start_year') : 1, filters.get('end_year') : 1}
			lft, rgt, root_type = frappe.db.get_value("Account", account[0][0], ['lft', 'rgt', 'root_type'])
			if start_year_closing := frappe.db.sql(
				f"""
						SELECT
							IFNULL(SUM(debit - credit), 0) as closing_balance
						FROM
							`tabGL Entry`
						WHERE
							posting_date <= '{start_year_date}' and company = '{filters.get('company')}' and account in (select name from `tabAccount` where lft >= '{lft}' and rgt <= '{rgt}')
				""",
				as_dict=1,
			):
				closing_dict[row][filters.get('start_year')] = flt(start_year_closing[0]['closing_balance'])
				if root_type in ['Liability', 'Income']:
					closing_dict[row][filters.get('start_year')] = (-1) * closing_dict[row][filters.get('start_year')]

			if end_year_closing := frappe.db.sql(
				f"""
						SELECT
							IFNULL(SUM(debit - credit), 0) as closing_balance
						FROM
							`tabGL Entry`
						WHERE
							posting_date <= '{end_year_date}' and company = '{filters.get('company')}' and account in (select name from `tabAccount` where lft >= '{lft}' and rgt <= '{rgt}')
				""",
				as_dict=1,
			):
				closing_dict[row][filters.get('end_year')] = flt(end_year_closing[0]['closing_balance'])
				if root_type in ['Liability', 'Income']:
					closing_dict[row][filters.get('end_year')] = (-1) * closing_dict[row][filters.get('end_year')]

	for key, value in account_dict.items():
		if closing_dict:
			fiscal_year1, fiscal_year2 = 0, 0
			account_lst = [closing_dict[value[i]]['account'] for i in range(len(value))]
			numerator_denominator = ",".join(account_lst)
			if key not in ["quick_ratio_section", "net_profit_ratio_section"]:
				if closing_dict[value[1]][filters.get('start_year')] != 0:
					fiscal_year1 = closing_dict[value[0]][filters.get('start_year')] / (closing_dict[value[1]][filters.get('start_year')])
				if closing_dict[value[1]][filters.get('end_year')] != 0:
					fiscal_year2 = closing_dict[value[0]][filters.get('end_year')] / (closing_dict[value[1]][filters.get('end_year')])
			
			elif key == "quick_ratio_section":
				if closing_dict[value[2]][filters.get('start_year')] != 0:
					fiscal_year1 = (closing_dict[value[0]][filters.get('start_year')] - closing_dict[value[1]][filters.get('start_year')] - closing_dict[value[3]][filters.get('start_year')]) / (closing_dict[value[2]][filters.get('start_year')] or 1)
				if closing_dict[value[2]][filters.get('end_year')] != 0:
					fiscal_year2 = (closing_dict[value[0]][filters.get('end_year')] - closing_dict[value[1]][filters.get('end_year')] - closing_dict[value[3]][filters.get('end_year')]) / (closing_dict[value[2]][filters.get('end_year')] or 1)

			elif key == "net_profit_ratio_section":
				if closing_dict[value[1]][filters.get('start_year')] != 0:
					fiscal_year1 = closing_dict[value[0]][filters.get('start_year')] / (closing_dict[value[1]][filters.get('start_year')] or 1) * 100
				if closing_dict[value[1]][filters.get('end_year')] != 0:
					fiscal_year2 = closing_dict[value[0]][filters.get('end_year')] / (closing_dict[value[1]][filters.get('end_year')] or 1) * 100
			
			variance = 0
			if round(fiscal_year1, 2) != 0:
				variance = ((round(fiscal_year2, 2) - round(fiscal_year1, 2)) / round(fiscal_year1, 2)) * 100
			data.append({'ratio' : frappe.unscrub(key.replace('_section', '')), 'numerator_denominator': numerator_denominator, filters.get('start_year') : fiscal_year1, filters.get('end_year') : fiscal_year2, 'variance' : variance})

	return  data