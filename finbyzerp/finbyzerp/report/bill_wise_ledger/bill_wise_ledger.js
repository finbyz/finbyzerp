// Copyright (c) 2022, FinByz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Bill Wise Ledger"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "report_date",
			"label": __("Posting Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "finance_book",
			"label": __("Finance Book"),
			"fieldtype": "Link",
			"options": "Finance Book"
		},
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			get_query: () => {
				var company = frappe.query_report.get_filter_value('company');
				return {
					filters: {
						'company': company
					}
				};
			}
		},
		{
			"fieldname": "party_type",
			"label": __("Party Type"),
			"fieldtype": "Select",
			"options": "Customer\nSupplier",
			"reqd":1,
			"default" : "Supplier",
			on_change : () => {
				let filter_based_on = frappe.query_report.get_filter_value('party_type');
				frappe.query_report.toggle_filter_display('customer', filter_based_on === 'Supplier');
				frappe.query_report.toggle_filter_display('customer_group', filter_based_on === 'Supplier');
				frappe.query_report.toggle_filter_display('supplier', filter_based_on === 'Customer');
				frappe.query_report.toggle_filter_display('supplier_group', filter_based_on === 'Customer');
				frappe.query_report.set_filter_value('customer', null);
				frappe.query_report.set_filter_value('supplier', null);
				frappe.query_report.set_filter_value('customer_group', null);
				frappe.query_report.set_filter_value('supplier_group', null);
				frappe.query_report.refresh();
			}
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"hidden" : 1
		},
		{
			"fieldname": "supplier",
			"label": __("Supplier"),
			"fieldtype": "Link",
			"options": "Supplier"
		},
		{
			"fieldname": "party_account",
			"label": __("Receivable Account"),
			"fieldtype": "Link",
			"options": "Account",
			get_query: () => {
				var company = frappe.query_report.get_filter_value('company');
				return {
					filters: {
						'company': company,
						'account_type': 'Receivable',
						'is_group': 0
					}
				};
			},

		},
		{
			"fieldname": "ageing_based_on",
			"label": __("Ageing Based On"),
			"fieldtype": "Select",
			"options": 'Posting Date\nDue Date',
			"default": "Due Date"
		},
		{
			"fieldname": "customer_group",
			"label": __("Customer Group"),
			"fieldtype": "Link",
			"options": "Customer Group",
			"hidden" : 1
		},
		{
			"fieldname": "supplier_group",
			"label": __("Supplier Group"),
			"fieldtype": "Link",
			"options": "Supplier Group"
		},
		{
			"fieldname": "payment_terms_template",
			"label": __("Payment Terms Template"),
			"fieldtype": "Link",
			"options": "Payment Terms Template"
		},
		{
			"fieldname": "sales_partner",
			"label": __("Sales Partner"),
			"fieldtype": "Link",
			"options": "Sales Partner"
		},
		{
			"fieldname": "sales_person",
			"label": __("Sales Person"),
			"fieldtype": "Link",
			"options": "Sales Person"
		},
		{
			"fieldname": "territory",
			"label": __("Territory"),
			"fieldtype": "Link",
			"options": "Territory"
		},
		{
			"fieldname": "group_by_party",
			"label": __("Group By Party"),
			"fieldtype": "Check"
		},
		{
			"fieldname": "based_on_payment_terms",
			"label": __("Based On Payment Terms"),
			"fieldtype": "Check",
			"hidden": 1
		},
		{
			"fieldname": "show_future_payments",
			"label": __("Show Future Payments"),
			"fieldtype": "Check",
			"hidden": 1
		},
		{
			"fieldname": "show_delivery_notes",
			"label": __("Show Linked Delivery Notes"),
			"fieldtype": "Check",
			"hidden": 1
		},
		{
			"fieldname": "show_sales_person",
			"label": __("Show Sales Person"),
			"fieldtype": "Check",
		},
		{
			"fieldname": "show_remarks",
			"label": __("Show Remarks"),
			"fieldtype": "Check",
		},
		{
			"fieldname": "show_all_invoices",
			"label": __("Show All Invoices"),
			"fieldtype": "Check"
		},
		{
			"fieldname": "tax_id",
			"label": __("Tax Id"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname": "customer_name",
			"label": __("Customer Name"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname": "supplier_name",
			"label": __("Supplier Name"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname": "payment_terms",
			"label": __("Payment Tems"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname": "credit_limit",
			"label": __("Credit Limit"),
			"fieldtype": "Currency",
			"hidden": 1
		}
	],

	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.bold){
			value = value.bold();
		}
		return value;
	}
};