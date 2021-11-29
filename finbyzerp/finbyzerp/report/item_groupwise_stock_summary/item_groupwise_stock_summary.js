// Copyright (c) 2016, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */
frappe.query_reports["Item Groupwise Stock Summary"] = {
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
			"default":frappe.defaults.get_user_default("year_start_date"),
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"r,eqd": 1
		},
		{
			"fieldname":"cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			get_query: () => {
				var company = frappe.query_report.get_filter_value('company');
				return {
					filters: {
						'company': company
					}
				}
			}
		},
		{
			"fieldname":"purchase",
			"label": __("Purchase"),
			"fieldtype": "Check",
		},
		{
			"fieldname":"sales",
			"label": __("Sales"),
			"fieldtype": "Check",
		},

	],
	"tree": true,
	"name_field": "item_group",
	"parent_field": "parent_item_group",
	"initial_depth": 1,
	"formatter": function(value, row, column, data, default_formatter) {
		if (column.fieldname=="item_group") {
			value = data.item_group || value;

			column.is_tree = true;
		}

		value = default_formatter(value, row, column, data);

		if (!data.parent_item_group) {
			value = $(`<span>${value}</span>`);

			var $value = $(value).css("font-weight", "bold");
			if (data.warn_if_negative && data[column.fieldname] < 0) {
				$value.addClass("text-danger");
			}

			value = $value.wrap("<p></p>").parent().html();
		}

		return value;
	},
};