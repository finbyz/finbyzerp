// Copyright (c) 2016, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock GL and SLE Difference"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Company",
			"default": frappe.defaults.get_default("company")
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		// {
		// 	"fieldname": "warehouse",
		// 	"label": __("Warehouse"),
		// 	"fieldtype": "Link",
		// 	"width": "80",
		// 	"options": "Warehouse",
		// 	"get_query": function() {
		// 		var company = frappe.query_report.get_filter_value('company');
		// 		return {
		// 			"doctype": "Warehouse",
		// 			"filters": {
		// 				"company": company,
		// 			}
		// 		}
		// 	}
		// },
		{
			"fieldname": "account",
			"label": __("Account"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Account",
			"get_query": function() {
				var company = frappe.query_report.get_filter_value('company');
				return {
					"doctype": "Account",
					"filters": {
						"company": company,
					}
				}
			}
		},
	]
};
