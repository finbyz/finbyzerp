// Copyright (c) 2016, FinByz and contributors
// For license information, please see license.txt
/* eslint-disable */
// var dt = frappe.db.get_value("Fiscal Year",frappe.sys_defaults.fiscal_year,'start_date',function(r){
// 	return r.start_date
// })
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
};
frappe.query_reports["Monthly Stock Summary"] = {
	onload: function() {
		var item_code = getUrlParameter("item_code");
		var item_group = getUrlParameter('item_group');
		var warehouse = getUrlParameter('warehouse');
		if(item_group){
			frappe.query_report.set_filter_value('item_group', item_group);
		}
		if(warehouse){
			frappe.query_report.set_filter_value('warehouse', warehouse);
		}
		if(item_code){
			frappe.query_report.set_filter_value('item_code', item_code);
		}
	},
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
	]
};
