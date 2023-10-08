frappe.query_reports["Delivery Note Trends"] = {
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
			"fieldname":"based_on",
			"label": __("Based On"),
			"fieldtype": "Select",
			"options": [
				{ "value": "Item", "label": __("Item") },
				{ "value": "Item Group", "label": __("Item Group") },
				{ "value": "Customer", "label": __("Customer") },
				{ "value": "Customer Group", "label": __("Customer Group") },
				{ "value": "Territory", "label": __("Territory") },
				{ "value": "Project", "label": __("Project") }
			],
			"default": "Item",
			"dashboard_config": {
				"read_only": 1,
			},
			"on_change": function(){
				if (frappe.query_report.get_filter_value('based_on')== "Item" ){
					frappe.query_report.get_filter('item').toggle(true)
				}
				else{
					frappe.query_report.get_filter('item').toggle(false)
				}

				if (frappe.query_report.get_filter_value('based_on')== "Item Group" ){
					frappe.query_report.get_filter('item_group').toggle(true)
				}
				else{
					frappe.query_report.get_filter('item_group').toggle(false)
				}

				if (frappe.query_report.get_filter_value('based_on')== "Customer" ){
					frappe.query_report.get_filter('customer').toggle(true)
				}
				else{
					frappe.query_report.get_filter('customer').toggle(false)
				}

				if (frappe.query_report.get_filter_value('based_on')== "Customer Group" ){
					frappe.query_report.get_filter('customer_group').toggle(true)
				}
				else{
					frappe.query_report.get_filter('customer_group').toggle(false)
				}

				if (frappe.query_report.get_filter_value('based_on')== "Cost-Center" ){
					frappe.query_report.get_filter('cost_center').toggle(true)
				}
				else{
					frappe.query_report.get_filter('cost_center').toggle(false)
				}
				frappe.query_report.refresh()
			}
		},
		{
			"fieldname":"group_by",
			"label": __("Group By"),
			"fieldtype": "Select",
			"options": [
				"",
				{ "value": "Item", "label": __("Item") },
				{ "value": "Customer", "label": __("Customer") }
			],
			"default": ""
		},
		{
			"fieldname":"fiscal_year",
			"label": __("Fiscal Year"),
			"fieldtype": "Link",
			"options":'Fiscal Year',
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname":"customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"hidden":1
		},
		{
			"fieldname":"customer_group",
			"label": __("Customer Group"),
			"fieldtype": "Link",
			"options": "Customer Group",
			"hidden":1
		},
		{
			"fieldname":"item",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname":"item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group",
			"hidden":1
		},
	]
};