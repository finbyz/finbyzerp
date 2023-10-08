frappe.query_reports["Purchase Receipt Trends"] = {
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
			"fieldname":"period_based_on",
			"label": __("Period based On"),
			"fieldtype": "Select",
			"options": [
				{ "value": "posting_date", "label": __("Posting Date") },
				{ "value": "bill_date", "label": __("Billing Date") },
			],
			"default": "posting_date"
		},
		{
			"fieldname":"based_on",
			"label": __("Based On"),
			"fieldtype": "Select",
			"options": [
				{ "value": "Item", "label": __("Item") },
				{ "value": "Item Group", "label": __("Item Group") },
				{ "value": "Supplier", "label": __("Supplier") },
				{ "value": "Supplier Group", "label": __("Supplier Group") },
				{ "value": "Project", "label": __("Project") }
			],
			"default": "Item",
			"dashboard_config": {
				"read_only": 1
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

				if (frappe.query_report.get_filter_value('based_on')== "Supplier" ){
					frappe.query_report.get_filter('supplier').toggle(true)
				}
				else{
					frappe.query_report.get_filter('supplier').toggle(false)
				}

				if (frappe.query_report.get_filter_value('based_on')== "Supplier Group" ){
					frappe.query_report.get_filter('supplier_group').toggle(true)
				}
				else{
					frappe.query_report.get_filter('supplier_group').toggle(false)
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
				{ "value": "Supplier", "label": __("Supplier") }
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
			"fieldname":"supplier",
			"label": __("Supplier"),
			"fieldtype": "Link",
			"options": "Supplier",
			"hidden":1
		},
		{
			"fieldname":"supplier_group",
			"label": __("Supplier Group"),
			"fieldtype": "Link",
			"options": "Supplier Group",
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
}