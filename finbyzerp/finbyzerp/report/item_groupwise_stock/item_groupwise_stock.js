frappe.require("assets/erpnext/js/financial_statements.js", function() {
	frappe.query_reports["Item Groupwise Stock"] = {
		"filters": [
			{
				"fieldname": "company",
				"label": __("Company"),
				"fieldtype": "Link",
				"options": "Company",
				"default": frappe.defaults.get_user_default("Company"),
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
			// {
			// 	"fieldname":"authorized",
			// 	"label": __("Authorized"),
			// 	"fieldtype": "Check",				
			// },
			// {
			// 	"fieldname":"unauthorized",
			// 	"label": __("Unauthorized"),
			// 	"fieldtype": "Check",
			// 	"default":1	
			// },
			{
				"fieldname":"show_0_qty_inventory",
				"label": __("Show 0 Qty Inventory"),
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
	
				column.link_onclick =
					"erpnext.financial_statements.open_general_ledger(" + JSON.stringify(data) + ")";
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
			
			if (column.fieldname == "balance_qty" && data && data.balance_qty < 0) {
				value = "<span style='color:red'>" + value + "</span>";
			}
			if (column.fieldname == "balance_value" && data && data.balance_value < 0) {
				value = "<span style='color:red'>" + value + "</span>";
			}


			return value;
		},
	}
});

// function route_to_sbe(company,item_group){

// 	frappe.set_route("query-report", "Stock Ledger Engineering",{
// 		"company": company,
// 		"item_group": item_group
	
// 	});
// }
// function route_to_sle_item(company, item_name ){
// 	// frappe.route_options = {
// 	// 	item_group: me.frm.doc.item_group,
// 	// 	company: me.frm.doc.company
// 	// };
// 	frappe.set_route("query-report", "Stock Ledger Engineering",{
// 		"company": company,
// 		"item_code": item_name
// 	}); "item_code=" + item_name
// }

function route_to_sle(company, warehouse, item_group) {
	if (warehouse){
		window.open(window.location.href.split('app')[0] + "app/query-report/Stock Ledger" + "/?" + "company=" + company + "&" + "warehouse="+ warehouse + "&" +"item_group="+item_group,"_blank")	
	}else{
		window.open(window.location.href.split('app')[0] + "app/query-report/Stock Ledger" + "/?" + "company=" + company + "&" +  "item_group="+item_group,"_blank")	
	}
}

function route_to_sle_item(company, warehouse, item_name) {
	if (warehouse){
		window.open(window.location.href.split('app')[0] + "app/query-report/Stock Ledger" + "/?" + "company="+company + "&" + "warehouse="+ warehouse + "&" + "item_code=" + item_name,"_blank")	
	}else{
		window.open(window.location.href.split('app')[0] + "app/query-report/Stock Ledger" + "/?" + "company="+company + "&" + "item_code=" + item_name,"_blank")	
	}
}

function route_to_stock_balance(company, warehouse, item_group) {
	if (warehouse){
		window.open(window.location.href.split('app')[0] + "app/query-report/Stock Balance" + "/?" + "company=" + company + "&" +  "warehouse="+ warehouse + "&" + "show_warehouse_wise_balance=1" + "&" +"item_group="+item_group,"_blank")	
	}
	else{
		window.open(window.location.href.split('app')[0] + "app/query-report/Stock Balance" + "/?" + "company=" + company + "&" +  "item_group="+item_group,"_blank")	
	}
}

function route_to_stock_balance_item(company, warehouse, item_name) {
	if (warehouse){
		window.open(window.location.href.split('app')[0] + "app/query-report/Stock Balance" + "/?" + "company="+company + "&" + "warehouse="+ warehouse + "&" + "show_warehouse_wise_balance=1" + "&" + "item_code=" + item_name,"_blank")	
	}
	else{
		window.open(window.location.href.split('app')[0] + "app/query-report/Stock Balance" + "/?" + "company="+company + "&" + "item_code=" + item_name,"_blank")	
	}
}

function route_to_monthly_stock_balance(company, item_group) {
	window.open(window.location.href.split('app')[0] + "app/query-report/Monthly Stock Summary" + "/?" + "company=" + company + "&" +  "item_group="+item_group,"_blank")	
}

function route_to_monthly_stock_balance_item(company, item_name) {
	window.open(window.location.href.split('app')[0] + "app/query-report/Monthly Stock Summary" + "/?" + "company="+company + "&" + "item_code=" + item_name,"_blank")	
}