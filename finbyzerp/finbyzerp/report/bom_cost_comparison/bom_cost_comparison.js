// Copyright (c) 2022, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["BOM Cost Comparison"] = {
	"filters": [
		{
			"fieldname":"item",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"reqd": 1
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"bom",
			"label": __("BOM"),
			"fieldtype": "MultiSelectList",
			"get_data": function(txt) {
				return frappe.db.get_link_options("BOM", txt);
			},
			get_data: function(txt) {
				return frappe.db.get_link_options('BOM', txt, {
					item: frappe.query_report.get_filter_value("item"),
					docstatus : 1
				});
			}
		},
		{
			"fieldname":"price_list",
			"label": __("Price List"),
			"fieldtype": "Link",
			"options" : "Price List",
			"reqd" : 1
		}
	]
};
