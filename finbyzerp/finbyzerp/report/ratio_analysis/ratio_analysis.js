// Copyright (c) 2023, FinByz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Ratio Analysis"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"reqd": 1,
			"options": "Company",
		},
		{
			"fieldname": "start_year",
			"label": __("Start Year"),
			"fieldtype": "Link",
			"reqd": 1,
			"options": "Fiscal Year",
		},
		{
			"fieldname": "end_year",
			"label": __("End Year"),
			"fieldtype": "Link",
			"reqd": 1,
			"options": "Fiscal Year",
		},
	]
};
