// Copyright (c) 2016, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Invoices Without Delivery OR Receipt"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname":"doctype",
			"label": __("Doctype"),
			"fieldtype": "Select",
			"options": "Sales\nPurchase",
			"reqd": 1,
			"default":"Sales"
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("year_start_date")
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.defaults.get_user_default("year_end_date")
		},
		// {
		// 	"fieldname":"show_only_invoice_data",
		// 	"label": __("Show Only Invoice Data"),
		// 	"fieldtype": "Check",
		// 	"default":0
		// },
	]
};
