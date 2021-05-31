// Copyright (c) 2016, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["BOM Stock Calculation"] = {
	"filters": [
		{
			"fieldname": "bom",
			"label": __("BOM"),
			"fieldtype": "Link",
			"options": "BOM",
			"reqd": 1
		},
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
		},
		{
			"fieldname": "qty_to_make",
			"label": __("Quantity to Make"),
			"fieldtype": "Int",
			"default": "1"
		},
		{
			"fieldname": "show_exploded_view",
			"label": __("Show exploded view"),
			"fieldtype": "Check"
		},
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.id == "item") {
			if (data["enough_parts_to_build"] > 0) {
				value = `<a style='color:green' href="/app/item/${data['item']}" data-doctype="Item">${data['item']}</a>`;
			} else {
				value = `<a style='color:red' href="/app/item/${data['item']}" data-doctype="Item">${data['item']}</a>`;
			}
		}
		return value
	}};
