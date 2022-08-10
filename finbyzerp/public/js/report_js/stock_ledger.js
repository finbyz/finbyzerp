// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
};
frappe.query_reports["Stock Ledger"] = {
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
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
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
			"fieldname":"warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
			"get_query": function() {
				const company = frappe.query_report.get_filter_value('company');
				return {
					filters: { 'company': company }
				}
			}
		},
		{
			"fieldname":"item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"get_query": function() {
				return {
					query: "erpnext.controllers.queries.item_query"
				}
			}
		},
		{
			"fieldname":"item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group"
		},
		{
			"fieldname":"batch_no",
			"label": __("Batch No"),
			"fieldtype": "Link",
			"options": "Batch"
		},
		{
			"fieldname":"brand",
			"label": __("Brand"),
			"fieldtype": "Link",
			"options": "Brand"
		},
		{
			"fieldname":"voucher_no",
			"label": __("Voucher #"),
			"fieldtype": "Data"
		},
		{
			"fieldname":"project",
			"label": __("Project"),
			"fieldtype": "Link",
			"options": "Project"
		},
		{
			"fieldname":"include_uom",
			"label": __("Include UOM"),
			"fieldtype": "Link",
			"options": "UOM"
		}
	],
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname == "outward_qty" && data && data.outward_qty != 0) {
			value =  `<span style='color:red; font-weight: bold;'>${value}</span>`;
		}
		else if (column.fieldname == "inward_qty" && data && data.inward_qty != 0) {
			value = `<span style='color:green; font-weight: bold;'>${value}</span>`;
		}
        else if (column.fieldname == "qty_after_transaction" && data && data.qty_after_transaction != 0) {
			value = `<span style='font-weight: bold;'>${value}</span>`;
		}
		return value;
	},
}
