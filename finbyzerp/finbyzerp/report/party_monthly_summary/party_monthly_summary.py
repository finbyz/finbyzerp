# Copyright (c) 2013, FinByz and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from fileinput import close
from multiprocessing import Condition
from dataclasses_json import config
import frappe
from frappe.utils import getdate
from dateutil.relativedelta import relativedelta

from itertools import zip_longest

def execute(filters=None):
	columns, data = [], []
	columns = [
		{
			"fieldname": "month",
			"label": ("Month"),
			"fieldtype": "Data",
			"width": 100
		},
		# {
		# 	"fieldname": "opening_balance",
		# 	"label": ("Opening Balance"),
		# 	"fieldtype": "Currency",
		# 	"width": 120,
		# },
		{
			"fieldname": "debit",
			"label": ("Debit"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "credit",
			"label": ("Credit"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "closing_balance",
			"label": ("Closing Balance"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "general_ledger",
			"label": ("General Ledger"),
			"fieldtype": "button",
			"width": 180
		}
		]

	data = get_data(filters)
	return columns, data

def get_mon(dt):
	return getdate(dt).strftime("%b")

def diff_month(d1, d2):
	return (d1.year - d2.year) * 12 + d1.month - d2.month

def get_data(filters):
	date_range = get_period_date_ranges(filters.get('period'),getdate(filters.get('from_date')),getdate(filters.get('to_date')))

	month_list = []
	if date_range:
		for dt in date_range:
			if filters.get('period') == "Monthly" and get_mon(dt[0])+'-'+dt[0].strftime("%y") not in month_list:
				month_list.append(get_mon(dt[0])+'-'+dt[0].strftime("%y"))
			if filters.get('period') != "Monthly" and (get_mon(dt[0])+'-'+dt[0].strftime("%y")) + "-" + (get_mon(dt[1]))+'-'+dt[1].strftime("%y") not in month_list:
				month_list.append((get_mon(dt[0])+'-'+dt[0].strftime("%y")) + "-" + (get_mon(dt[1]))+'-'+dt[1].strftime("%y"))

	result = {month_list[i]: date_range[i] for i in range(len(month_list))}

	conditions = ""

	conditions += f" and company = '{filters.get('company')}'"
	conditions += f" and party_type = '{filters.get('party_type')}'"
	conditions += f" and party = '{filters.get('party')}'"
	conditions += f" and is_cancelled = 0"
	if filters.get("cost_center"):
		conditions += f" and cost_center = '{filters.get('cost_center')}'"

	opening_data = frappe.db.sql(f"""
		SELECT
			SUM(credit) as credit, SUM(debit) as debit, sum(debit - credit) as closing_balance
		FROM
			`tabGL Entry`
		WHERE
			(posting_date < '{filters.get('from_date')}' or is_opening = 'Yes')
		{conditions}
	""", as_dict =1)

	party_data = []
	closing_data = []
	
	for month, date in result.items():
		party_details = frappe.db.sql(f"""
			SELECT 
				IFNULL(IF(is_opening = "YES", 0, sum(credit)),0) as credit, IFNULL(IF(is_opening = "YES", 0,SUM(debit)), 0) as debit
			FROM
				`tabGL Entry`
			WHERE
				posting_date >= '{date[0]}' and posting_date <= '{date[1]}'
				{conditions}
			GROUP BY
				party
		""", as_dict = 1)

		if party_details:
			party_data.append(party_details)
		else:
			party_data.append([{"credit" : 0, "debit" : 0}])

		closing_details = frappe.db.sql(f"""
			SELECT
				IFNULL(SUM(debit - credit), 0) as closing_balance, '{month}' as month, '{date[0]}' as from_date, '{date[1]}' as to_date
			FROM
				`tabGL Entry`
			WHERE
				posting_date <= '{date[1]}'
				{conditions}
		""", as_dict =1)

		if closing_details:
			closing_data.append(closing_details)

	party_data_list = [row[0] for row in party_data if row]
	closing_data_list = [row[0] for row in closing_data if row]

	if opening_data:
		for row in opening_data:
			data = [{
				"month": "Opening",
				"debit": row.debit or 0,
				"credit": row.credit or 0,
				"closing_balance": row.closing_balance or 0
			}]

	data += [{**u, **v } for u, v in zip_longest(party_data_list, closing_data_list, fillvalue={})]

	for row in data:
		if row.get('month') != "Opening":
			row['general_ledger'] = f"""<button style='margin-left:5px;border:none;color: #fff; background-color: #1581E1; padding: 3px 5px;border-radius: 5px;'
				target="_blank" company = '{filters.get('company')}' from_date = '{row.get('from_date')}' to_date = '{row.get('to_date')}' party_type = '{filters.get('party_type')}'
				party = '{filters.get('party')}' cost_center = '{filters.get('cost_center')}'
				onClick=open_general_ledger(this.getAttribute('company'),this.getAttribute('from_date'),this.getAttribute('to_date'),this.getAttribute('party_type'),this.getAttribute('party'),this.getAttribute('cost_center'))>View General Ledger</button>"""

	return data

def get_period_date_ranges(period, year_start_date, year_end_date):
	from dateutil.relativedelta import relativedelta

	increment = {
		"Monthly": 1,
		"Quarterly": 3,
		"Half-Yearly": 6,
		"Yearly": 12
	}.get(period)
	diff = abs(diff_month(getdate(year_start_date),getdate(year_end_date)))
	period_date_ranges = []
	for i in range(1, diff+2, increment):
		period_end_date = getdate(year_start_date) + relativedelta(months=increment, days=-1)
		if period_end_date > getdate(year_end_date):
			period_end_date = year_end_date
		period_date_ranges.append([year_start_date, period_end_date])
		year_start_date = period_end_date + relativedelta(days=1)
		if period_end_date == year_end_date:
			break
	return period_date_ranges