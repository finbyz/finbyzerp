// Copyright (c) 2016, FinByz and contributors
// For license information, please see license.txt
/* eslint-disable */
// var dt = frappe.db.get_value("Fiscal Year",frappe.sys_defaults.fiscal_year,'start_date',function(r){
// 	return r.start_date
// })
frappe.query_reports["Monthly Stock Summary"] = {
	"filters": [
		{
			"fieldname":"period",
			"label": __("Period"),
			"fieldtype": "Select",
			"options": [
				{ "value": "Monthly", "label": __("Monthly") },
				{ "value": "Quarterly", "label": __("Quarterly") },
				{ "value": "Half-Yearly", "label": __("Half-Yearly") },
				{ "value": "Yearly", "label": __("Yearly") }
			],
			"default": "Monthly"
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default":frappe.defaults.get_user_default("year_start_date"),
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname":"item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname":"item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group"
		},
		{
			"fieldname":"show_profit",
			"label": __("Show Profit"),
			"fieldtype": "Check"
		},
		{
			"fieldname":"show_only_purchase_n_delivery_data",
			"label": __("Show Only Purchase & Delivery Data"),
			"fieldtype": "Check",
			"on_change": function(){
				if (frappe.query_report.get_filter_value('show_only_purchase_n_delivery_data') == 1){
					frappe.query_report.get_filter('item_group').toggle(false)
				} else {
					frappe.query_report.get_filter('item_group').toggle(true)
				}
				frappe.query_report.refresh();
			}
		},
	],
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname == "inward_value" && data && data.inward_value > 0) {
			value =  `<span style='color:green; font-weight: bold;'>${value}</span>`;
		}
		if (column.fieldname == "inward_qty" && data && data.inward_value > 0) {
			value =  `<span style='color:green; font-weight: bold;'>${value}</span>`;
		}
		if (column.fieldname == "outward_qty" && data && data.outward_value > 0) {
			value =  `<span style='color:red; font-weight: bold;'>${value}</span>`;
		}
		if (column.fieldname == "outward_value" && data && data.outward_value > 0){

			value  =  `<span style='color:red; font-weight: bold;'>${value}</span>`;
		}
		return value
	}
};
