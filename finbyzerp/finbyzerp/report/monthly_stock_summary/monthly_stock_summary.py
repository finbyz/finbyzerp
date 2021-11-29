# Copyright (c) 2013, FinByz and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
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
		{
			"fieldname": "inward_qty",
			"label": ("Inward Qty"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "inward_value",
			"label": ("Inward Value"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "outward_qty",
			"label": ("Outward Qty"),
			"fieldtype": "Float",
			"width": 150
		},
		{
			"fieldname": "outward_value",
			"label": ("Outward Value"),
			"fieldtype": "Currency",
			"width": 150
		}]

	if filters.get('show_profit'):
		columns +=[
		{
			"fieldname": "consumption",
			"label": ("Consumption"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "gross_profit",
			"label": ("Gross Profit"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "gross_profit_percent",
			"label": ("Gross Profit %"),
			"fieldtype": "Percent",
			"width": 150
		}
	]
		
	columns +=[{
		"fieldname": "closing_qty",
		"label": ("Closing Qty"),
		"fieldtype": "Float",
		"width": 150
	},
	{
		"fieldname": "closing_value",
		"label": ("Closing Value"),
		"fieldtype": "Currency",
		"width": 150
	}]

	data = get_data(filters)
	chart = get_chart_data(data,filters)
	return columns, data, None, chart

def get_mon(dt):
	return getdate(dt).strftime("%b")

def diff_month(d1, d2):
	return (d1.year - d2.year) * 12 + d1.month - d2.month

def get_data(filters):
	conditions = ''
	group_by_cond = 'i.item_group'

	if not filters.get("item_group") and not filters.get("item_code"):
		frappe.throw("Item code or Item group has to be selected to generate the report")

	if filters.get("company"):
		conditions += " and sle.company = %s" % frappe.db.escape(filters.get("company"))

	if filters.get("item_group"):
		conditions += " and i.item_group = %s" % frappe.db.escape(filters.get("item_group"))
		
	if filters.get("item_code"):
		conditions += " and sle.item_code = %s" % frappe.db.escape(filters.get("item_code"))
		group_by_cond = 'sle.item_code'

	date_range = get_period_date_ranges(filters.get('period'),getdate(filters.get('from_date')),getdate(filters.get('to_date')))
	#months = get_period_month_ranges(filters.get('period'),getdate(filters.get('from_date')),getdate(filters.get('to_date')))
	
	month_list = []
	for dt in date_range:
		if filters.get('period') == "Monthly" and get_mon(dt[0])+'-'+dt[0].strftime("%y") not in month_list:
			month_list.append(get_mon(dt[0])+'-'+dt[0].strftime("%y"))
		if filters.get('period') != "Monthly" and (get_mon(dt[0])+'-'+dt[0].strftime("%y")) + "-" + (get_mon(dt[1]))+'-'+dt[1].strftime("%y") not in month_list:
			month_list.append((get_mon(dt[0])+'-'+dt[0].strftime("%y")) + "-" + (get_mon(dt[1]))+'-'+dt[1].strftime("%y"))
				
	result = {month_list[i]: date_range[i] for i in range(len(month_list))}
	
	inward_data = []
	outward_data = []
	closing_data = []
	opening_data = []

	if filters.get('from_date'):
		opening_data = frappe.db.sql("""
			SELECT sum(sle.actual_qty) as closing_qty, sum(sle.stock_value_difference) as closing_value
			FROM `tabStock Ledger Entry` as sle
			LEFT JOIN `tabItem` as i ON i.name = sle.item_code
			where sle.is_cancelled = 0 and sle.posting_date < '{}' {}
		""".format(filters.get('from_date'),conditions),as_dict=True)

	for month, date in result.items():		
		inward_data.append(frappe.db.sql("""
			SELECT sum(sle.actual_qty) as inward_qty, sum(sle.incoming_rate*sle.actual_qty) as inward_value, '{}' as month
			FROM `tabStock Ledger Entry` as sle
			LEFT JOIN `tabStock Entry Detail` as se ON se.name = sle.voucher_detail_no
			LEFT JOIN `tabItem` as i ON i.name = sle.item_code
			WHERE sle.is_cancelled = 0 and sle.actual_qty > 0 and sle.posting_date BETWEEN '{}' AND '{}' and (se.t_warehouse IS NULL or se.s_warehouse IS NULL) {}
			group by {}
		""".format(month,date[0],date[1],conditions,group_by_cond),as_dict=True))

	
		outward_data.append(frappe.db.sql("""
			SELECT sum(Abs(sle.actual_qty)) as outward_qty, sum(Abs(sle.stock_value_difference)) as consumption,
			sum(IFNULL(si.amount, IFNULL(dn.amount, IFNULL(se.amount, Abs(sle.stock_value_difference))))) as outward_value,
			(sum(IFNULL(si.amount, IFNULL(dn.amount, IFNULL(se.amount, Abs(sle.stock_value_difference)))))-sum(Abs(sle.stock_value_difference))) as gross_profit,
			(((sum(IFNULL(si.amount, IFNULL(dn.amount, IFNULL(se.amount, Abs(sle.stock_value_difference)))))-sum(Abs(sle.stock_value_difference)))/sum(Abs(sle.stock_value_difference))) * 100) as gross_profit_percent,
			'{}' as month
			FROM `tabStock Ledger Entry`as sle
			LEFT JOIN `tabSales Invoice Item` as si ON si.name = sle.voucher_detail_no
			LEFT JOIN `tabDelivery Note Item` as dn ON dn.name = sle.voucher_detail_no
			LEFT JOIN `tabStock Entry Detail` as se ON se.name = sle.voucher_detail_no
			LEFT JOIN `tabItem` as i ON i.name = sle.item_code
			WHERE sle.is_cancelled = 0 and sle.actual_qty < 0  and sle.posting_date BETWEEN '{}' AND '{}' and (se.t_warehouse IS NULL or se.s_warehouse IS NULL) {}
			group by {}
		""".format(month,date[0],date[1],conditions,group_by_cond),as_dict=True))

		closing_data.append(frappe.db.sql("""
			SELECT sum(sle.actual_qty) as closing_qty, sum(sle.stock_value_difference) as closing_value, '{}' as month
			FROM `tabStock Ledger Entry` as sle
			LEFT JOIN `tabItem` as i ON i.name = sle.item_code
			where sle.is_cancelled = 0 and sle.posting_date <= '{}' {}
		""".format(month,date[1],conditions),as_dict=True))

	
	in_data = [item[0] for item in inward_data if item]
	out_data = [item[0] for item in outward_data if item]
	close_data = [item[0] for item in closing_data if item]

	data = []

	if opening_data:
		for row in opening_data:
			data = [{
				"month": "Opening",
				"closing_qty": row.closing_qty,
				"closing_value": row.closing_value
			}]
	data += [{**u, **v, **m } for u, v, m in zip_longest(in_data, out_data, close_data, fillvalue={})]
	return data
	
def get_chart_data(data,filters):

	labels, inward_datapoints, outward_datapoints = [], [], []

	for row in data:
		labels.append(row.get('month'))
		inward_datapoints.append(row.get('inward_value') or 0.0)
		outward_datapoints.append(row.get('outward_value') or 0.0)

	datasets = []
	datasets.append({
		'name': "Inward",
		'values': inward_datapoints
	})
	datasets.append({
		'name': "Outward",
		'values': outward_datapoints
	})
	chart = {
		"data": {
			'labels': labels,
			'datasets': datasets
		}
	}
	chart["type"] = "bar"
	return chart

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

def get_period_month_ranges(period, year_start_date,year_end_date):
	from dateutil.relativedelta import relativedelta
	period_month_ranges = []

	for start_date, end_date in get_period_date_ranges(period, year_start_date,year_end_date):
		months_in_this_period = []
		while start_date <= end_date:
			months_in_this_period.append(start_date.strftime("%B")+ "-" +start_date.strftime("%y"))
			start_date += relativedelta(months=1)
		period_month_ranges.append(months_in_this_period)

	return period_month_ranges
