function get_sales_trends_filters() {
	return [
		{
			"fieldname": "period",
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
			"fieldname": "based_on",
			"label": __("Based On"),
			"fieldtype": "Select",
			"options": [
				{ "value": "Item", "label": __("Item") },
				{ "value": "Item Group", "label": __("Item Group") },
				{ "value": "Customer", "label": __("Customer") },
				{ "value": "Customer Group", "label": __("Customer Group") },
				{ "value": "Territory", "label": __("Territory") },
				{ "value": "Project", "label": __("Project") },
				{ "value": "Cost Center", "label": __("Cost Center") }

			],
			"default": "Item",
			"dashboard_config": {
				"read_only": 1,
			},
			"on_change": function () {
				if (frappe.query_report.get_filter_value('based_on') == "Item") {
					frappe.query_report.get_filter('item').toggle(true)
				}
				else {
					frappe.query_report.get_filter('item').toggle(false)
				}

				if (frappe.query_report.get_filter_value('based_on') == "Item Group") {
					frappe.query_report.get_filter('item_group').toggle(true)
				}
				else {
					frappe.query_report.get_filter('item_group').toggle(false)
				}

				if (frappe.query_report.get_filter_value('based_on') == "Customer") {
					frappe.query_report.get_filter('customer').toggle(true)
				}
				else {
					frappe.query_report.get_filter('customer').toggle(false)
				}

				if (frappe.query_report.get_filter_value('based_on') == "Customer Group") {
					frappe.query_report.get_filter('customer_group').toggle(true)
				}
				else {
					frappe.query_report.get_filter('customer_group').toggle(false)
				}

				if (frappe.query_report.get_filter_value('based_on') == "Cost Center") {
					frappe.query_report.get_filter('cost_center').toggle(true)
				}
				else {
					frappe.query_report.get_filter('cost_center').toggle(false)
				}
				frappe.query_report.refresh()
			}
		},
		{
			"fieldname": "group_by",
			"label": __("Group By"),
			"fieldtype": "Select",
			"options": [
				"",
				{ "value": "Item", "label": __("Item") },
				{ "value": "Customer", "label": __("Customer") },
				{ "value": "Item Group", "label": __("Item Group") }
			],
			"default": ""
		},
		{
			"fieldname": "fiscal_year",
			"label": __("Fiscal Year"),
			"fieldtype": "Link",
			"options": 'Fiscal Year',
			"default": erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), verbose = 0),
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"hidden": 1
		},
		{
			"fieldname": "customer_group",
			"label": __("Customer Group"),
			"fieldtype": "Link",
			"options": "Customer Group",
			"hidden": 1
		},
		{
			"fieldname": "item",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group",
			"hidden": 1
		},
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"hidden": 1
		},
	];
}

function get_purchase_trends_filters() {
	return [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "period",
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
			"fieldname": "fiscal_year",
			"label": __("Fiscal Year"),
			"fieldtype": "Link",
			"options": 'Fiscal Year',
			"default": erpnext.utils.get_fiscal_year(frappe.datetime.get_today())
		},
		{
			"fieldname": "period_based_on",
			"label": __("Period based On"),
			"fieldtype": "Select",
			"options": [
				{ "value": "posting_date", "label": __("Posting Date") },
				{ "value": "bill_date", "label": __("Billing Date") },
			],
			"default": "posting_date"
		},
		{
			"fieldname": "based_on",
			"label": __("Based On"),
			"fieldtype": "Select",
			"options": [
				{ "value": "Item", "label": __("Item") },
				{ "value": "Item Group", "label": __("Item Group") },
				{ "value": "Supplier", "label": __("Supplier") },
				{ "value": "Supplier Group", "label": __("Supplier Group") },
				{ "value": "Project", "label": __("Project") },
				{ "value": "Cost Center", "label": __("Cost Center") }
			],
			"default": "Item",
			"dashboard_config": {
				"read_only": 1
			},
			"on_change": function () {
				if (frappe.query_report.get_filter_value('based_on') == "Item") {
					frappe.query_report.get_filter('item').toggle(true)
				}
				else {
					frappe.query_report.get_filter('item').toggle(false)
				}

				if (frappe.query_report.get_filter_value('based_on') == "Item Group") {
					frappe.query_report.get_filter('item_group').toggle(true)
				}
				else {
					frappe.query_report.get_filter('item_group').toggle(false)
				}

				if (frappe.query_report.get_filter_value('based_on') == "Customer") {
					frappe.query_report.get_filter('customer').toggle(true)
				}
				else {
					frappe.query_report.get_filter('customer').toggle(false)
				}

				if (frappe.query_report.get_filter_value('based_on') == "Customer Group") {
					frappe.query_report.get_filter('customer_group').toggle(true)
				}
				else {
					frappe.query_report.get_filter('customer_group').toggle(false)
				}

				if (frappe.query_report.get_filter_value('based_on') == "Cost Center") {
					frappe.query_report.get_filter('cost_center').toggle(true)
				}
				else {
					frappe.query_report.get_filter('cost_center').toggle(false)
				}
				frappe.query_report.refresh()
			}
		},
		{
			"fieldname": "group_by",
			"label": __("Group By"),
			"fieldtype": "Select",
			"options": [
				"",
				{ "value": "Item", "label": __("Item") },
				{ "value": "Supplier", "label": __("Supplier") },
				{ "value": "Item Group", "label": __("Item Group") }
			],
			"default": ""
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"hidden": 1
		},
		{
			"fieldname": "customer_group",
			"label": __("Customer Group"),
			"fieldtype": "Link",
			"options": "Customer Group",
			"hidden": 1
		},
		{
			"fieldname": "item",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group",
			"hidden": 1
		},
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"hidden": 1
		},
	];
}

frappe.query_reports["Quotation Trends"] = {
	filters: get_sales_trends_filters()
}

frappe.query_reports["Sales Order Trends"] = {
	filters: get_sales_trends_filters()
}

frappe.query_reports["Delivery Note Trends"] = {
	filters: get_sales_trends_filters()
}

frappe.query_reports["Sales Invoice Trends"] = {
	filters: get_sales_trends_filters()
}

frappe.query_reports["Purchase Order Trends"] = {
	filters: get_purchase_trends_filters()
}

frappe.query_reports["Purchase Receipt Trends"] = {
	filters: get_purchase_trends_filters()
}

frappe.query_reports["Purchase Invoice Trends"] = {
	filters: get_purchase_trends_filters()
}
