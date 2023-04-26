// Copyright (c) 2021, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt


cur_frm.fields_dict.sales_taxes_and_charges.get_query = function (doc) {
	return {
		filters: {
			"company": doc.company,
		}
	}
};
cur_frm.fields_dict.purchase_taxes_and_charges.get_query = function (doc) {
	return {
		filters: {
			"company": doc.company,
		}
	}
};

cur_frm.fields_dict.items.grid.get_field("expense_account").get_query = function(doc) {
	return {
		filters: {
			"company": doc.company,
		}
	}
};

cur_frm.fields_dict.items.grid.get_field("income_account").get_query = function(doc) {
	return {
		filters: {
			"company": doc.company,
		}
	}
};


// Customer Address Filter
cur_frm.set_query("customer_address", function () {
    return {
        query: "frappe.contacts.doctype.address.address.address_query",
        filters: {
            link_doctype: "Customer",
            link_name: cur_frm.doc.party
        }
    };
});
cur_frm.set_query("supplier_address", function () {
    return {
        query: "frappe.contacts.doctype.address.address.address_query",
        filters: {
            link_doctype: "Supplier",
            link_name: cur_frm.doc.party
        }
    };
});
// Shipping Address Filter
cur_frm.set_query("shipping_address_name", function () {
    return {
        query: "frappe.contacts.doctype.address.address.address_query",
        filters: { link_doctype: "Customer", link_name: cur_frm.doc.party }
    };
});
// Customer Contact Filter
cur_frm.set_query("contact_person", function () {
    return {
        query: "frappe.contacts.doctype.contact.contact.contact_query",
        filters: { link_doctype: cur_frm.doc.party_type, link_name: cur_frm.doc.party }
    };
});

frappe.ui.form.on("Credit and Debit Note Item",{
	amount:function(frm, cdt, cdn) {
		var d=locals[cdt][cdn]
		frappe.model.set_value(d.doctype,d.name,"rate",d.amount)
		frappe.model.set_value(d.doctype,d.name,"base_amount",d.amount)
		frappe.model.set_value(d.doctype,d.name,"net_amount",d.amount)
		frappe.model.set_value(d.doctype,d.name,"base_net_amount",d.amount)
		frappe.model.set_value(d.doctype,d.name,"price_list_rate",d.amount)
		frappe.model.set_value(d.doctype,d.name,"base_price_list_rate",d.amount)
		frappe.model.set_value(d.doctype,d.name,"item_name",frm.doc.type)
		if (frm.doc.sales_taxes_and_charges || frm.doc.purchase_taxes_and_charges){
			Calculate_taxes_and_totals(frm);
		}
		
 	},
	item_tax_template:function(frm){
		if (frm.doc.sales_taxes_and_charges || frm.doc.purchase_taxes_and_charges){
			Calculate_taxes_and_totals(frm);
		}
	},
	items_add: function(frm,cdt,cdn){
		let d = locals[cdt][cdn]
		var df = frappe.meta.get_docfield("Credit and Debit Note Item","expense_account",d.name);
		if (frm.doc.party_type!="Customer"){
			df.reqd= 0;
		}
		else{
			df.reqd= 1;
		}
	}
});

frappe.ui.form.on("Credit and Debit Note", {
	refresh: function(frm){
		frm.add_custom_button(__("Reconcile"), function() {
			frm.reload_doc()
			frappe.set_route("Form","Payment Reconciliation")
			// window.open(window.location.href.split('app')[0] + "app/payment-reconciliation/Payment Reconciliation" + "/?" +"company="+frm.doc.company +"&" + "party_type="+frm.doc.party_type +"&"+ "party="+frm.doc.party,"_blank")	
		});
	},
	setup_queries(doc, cdt, cdn) {


		frm.set_query('supplier', erpnext.queries.supplier);
		frm.set_query('contact_person', erpnext.queries.contact_query);
		frm.set_query('supplier_address', erpnext.queries.address_query);

		frm.set_query('billing_address', erpnext.queries.company_address_query);

		if(frm.fields_dict.supplier) {
			frm.set_query("supplier", function() {
				return{	query: "erpnext.controllers.queries.supplier_query" }});
		}

		frm.set_query("item_code", "items", function() {
			if (frm.doc.is_subcontracted == "Yes") {
				return{
					query: "erpnext.controllers.queries.item_query",
					filters:{ 'supplier': frm.doc.supplier, 'is_sub_contracted_item': 1 }
				}
			}
			else {
				return{
					query: "erpnext.controllers.queries.item_query",
					filters: { 'supplier': frm.doc.supplier, 'is_purchase_item': 1 }
				}
			}
		});


		frm.set_query("manufacturer", "items", function(doc, cdt, cdn) {
			const row = locals[cdt][cdn];
			return {
				query: "erpnext.controllers.queries.item_manufacturer_query",
				filters:{ 'item_code': row.item_code }
			}
		});

		if(frm.fields_dict["items"].grid.get_field('item_code')) {
			frm.set_query("item_tax_template", "items", function(doc, cdt, cdn) {
				return set_query_for_item_tax_template(doc, cdt, cdn)
			});
		}
	},
	set_posting_time:function(frm){
		frm.set_df_property("posting_date",'read_only',!frm.doc.set_posting_time);
		frm.set_df_property("posting_time",'read_only',!frm.doc.set_posting_time);

		frm.refresh();
	},
	onload:function(frm){
		if (!frm.doc.posting_time){frm.set_value('posting_time', frappe.datetime.now_time());}
		
		frm.set_df_property("posting_date",'read_only',!frm.doc.set_posting_time);
		frm.set_df_property("posting_time",'read_only',!frm.doc.set_posting_time);
		frm.refresh();
		if (frm.doc.__islocal){
			var childTable = cur_frm.add_child("items");
			cur_frm.refresh_field("items")	
		}
		if (frm.doc.type=="Credit Note" && frm.doc.party_type=="Supplier")
		{
			frm.doc.is_return = 0;
		}
		else if (frm.doc.type=="Debit Note" && frm.doc.party_type=="Customer")
		{
			frm.doc.is_return = 0;
		}
		else{
			frm.doc.is_return = 1;
		}
		frm.refresh();
	},
	customer_address: function(frm) {
		erpnext.utils.get_address_display(frm, "customer_address", "address_display");
	},
	supplier_address: function(frm) {
		erpnext.utils.get_address_display(frm, "supplier_address", "address_display");
	},
	billing_address: function(frm) {
		erpnext.utils.get_address_display(frm, "billing_address", "billing_address_display");
	},
	shipping_address_name: function(frm) {
		erpnext.utils.get_address_display(frm, "shipping_address_name", "shipping_address");
	},
	// customer_address: function(frm) {
	// 	erpnext.utils.get_address_display(frm, "customer_address");
	// 	erpnext.utils.set_taxes_from_address(frm, "customer_address", "customer_address", "shipping_address_name");
	// },
	type:function(frm){
		if (frm.doc.type=="Credit Note" && frm.doc.party_type=="Supplier")
    {
        frm.doc.is_return = 0;
    }
    else if (frm.doc.type=="Debit Note" && frm.doc.party_type=="Customer")
    {
        frm.doc.is_return = 0;
    }
    else{
        frm.doc.is_return = 1;
    }
    frm.refresh();
	},
	party_type: function(frm){
		frm.doc.items.forEach(function(r){
			var df = frappe.meta.get_docfield("Credit and Debit Note Item","expense_account",r.name);
			if (frm.doc.party_type!="Customer"){
				df.reqd= 0;
			}
			else{
				df.reqd= 1;
			}
		})
		frm.refresh_field('items')

		frm.set_value("purchase_taxes_and_charges",'')
		frm.set_value("sales_taxes_and_charges",'')
		frm.set_value("purchase_taxes",'')
		frm.set_value("sales_taxes",'')
		frm.set_value("party",'')
		if (frm.doc.type=="Credit Note" && frm.doc.party_type=="Supplier")
		{
			frm.doc.is_return = 0;
		}
		else if (frm.doc.type=="Debit Note" && frm.doc.party_type=="Customer")
		{
			frm.doc.is_return = 0;
		}
		else{
			frm.doc.is_return = 1;
		}
		frm.refresh();
		// if (frm.doc.party_type == "Customer"){
		// 	// var taxes_and_charges_field = frappe.meta.get_docfield(frm.doc.doctype, "taxes_and_charges", frm.doc.name);
		// 	// var taxes_field = frappe.meta.get_docfield(frm.doc.doctype, "taxes", frm.doc.name);
		// 	// taxes_and_charges_field.options = "Sales Taxes and Charges Template";
		// 	// taxes_field.options = "Sales Taxes and Charges"
		// 	// frm.set_df_property("taxes_and_charges","options","Sales Taxes and Charges Template")
		// 	// frm.set_df_property("taxes","options","Sales Taxes and Charges")
		// }
		// if (frm.doc.party_type == "Supplier"){
		// 	// var taxes_and_charges_field = frappe.meta.get_docfield(frm.doc.doctype, "taxes_and_charges", frm.doc.name);
		// 	// var taxes_field = frappe.meta.get_docfield(frm.doc.doctype, "taxes", frm.doc.name);
		// 	// taxes_and_charges_field.options = "Purchase Taxes and Charges Template";
		// 	// taxes_field.options = "Purchase Taxes and Charges"
		// 	// frm.set_df_property("taxes_and_charges","options","Purchase Taxes and Charges Template")
		// 	// frm.set_df_property("taxes","options","Purchase Taxes and Charges")
		// }	
	},
	calculate_item_values:function(frm) {
	discount_amount_applied = false;
	if (!discount_amount_applied) {
		$.each(frm.doc["items"] || [], function(i, item) {
			frappe.model.round_floats_in(item);
			item.net_rate = item.rate;

			if ((!item.qty) && frm.doc.is_return) {
				item.amount = flt(item.rate * 1, precision("amount", item));
			} else {
				item.amount = flt(item.rate * item.qty, precision("amount", item));
			}

			item.net_amount = item.amount;
			item.item_tax_amount = 0.0;
			item.total_weight = flt(item.weight_per_unit * item.stock_qty);

			set_in_company_currency(frm,item, ["price_list_rate", "rate", "amount", "net_rate", "net_amount"]);
		});
	}
},
	purchase_taxes_and_charges: function(frm){
		if(frm.doc.purchase_taxes_and_charges) {
			frm.call({
				method: "erpnext.controllers.accounts_controller.get_taxes_and_charges",
				args: {
					"master_doctype": frappe.meta.get_docfield(frm.doc.doctype, "purchase_taxes_and_charges",
						frm.doc.name).options,
					"master_name": frm.doc.purchase_taxes_and_charges
				},
				callback: function(r) {
					if(!r.exc) {
						frm.set_value("purchase_taxes", r.message);
						refresh_field("purchase_taxes");
						Calculate_taxes_and_totals(frm);
					}
				}
			});
			
		}
	},
	sales_taxes_and_charges: function(frm){
		if(frm.doc.sales_taxes_and_charges) {
			frm.call({
				method: "erpnext.controllers.accounts_controller.get_taxes_and_charges",
				args: {
					"master_doctype": frappe.meta.get_docfield(frm.doc.doctype, "sales_taxes_and_charges",
						frm.doc.name).options,
					"master_name": frm.doc.sales_taxes_and_charges
				},
				callback: function(r) {
					if(!r.exc) {
						frm.set_value("sales_taxes", r.message);
						refresh_field("sales_taxes");
						Calculate_taxes_and_totals(frm);
					}
				}
			});
			
		}
		
		
	},
});



function Calculate_taxes_and_totals(frm){
	// calculate_item_price(frm);
	frappe.flags.round_off_applicable_accounts = [];
	if(frm.doc.party_type == "Customer"){
		frm.doc.taxes = frm.doc.sales_taxes
		frm.doc.taxes_and_charges = frm.doc.sales_taxes_and_charges 
	}
	else{
		frm.doc.taxes_and_charges = frm.doc.purchase_taxes_and_charges
		frm.doc.taxes = frm.doc.purchase_taxes
	}
	var discount_amount_applied = false;
	validate_conversion_rate(frm);
	calculate_item_values(frm);
	calculate_net_total(frm);
	initialize_taxes(frm);
	determine_exclusive_rate(frm);
	calculate_taxes(frm);
	manipulate_grand_total_for_inclusive_tax(frm);
	calculate_totals(frm);
	_cleanup(frm);
	
	if(frm.doc.party_type == "Customer"){
		frm.doc.sales_taxes = frm.doc.taxes
		frm.doc.sales_taxes_and_charges = frm.doc.taxes_and_charges
		frm.set_value("sales_taxes_and_charges",frm.doc.taxes_and_charges)
		frm.refresh();
	}
	else{
		frm.doc.purchase_taxes_and_charges = frm.doc.taxes_and_charges
		frm.doc.purchase_taxes = frm.doc.taxes
		frm.set_value("purchase_taxes_and_charges",frm.doc.taxes_and_charges)
		frm.refresh();
	}
	delete frm.doc['taxes']
	// return frappe.call({
	// 	method:"calculate_debit_credit_taxes",
	// 	doc:frm.doc,
	// 	callback:function(r){
	// 		// console.log(r.docs[0].sales_taxes)
	// 		frm.set_value("sales_taxes",'')
			
	// 		frm.set_value("sales_taxes",r.docs[0].sales_taxes);
	// 		// frm.set_value("purchase_taxes",r.docs[0].purchase_taxes);
	// 		// frm.set_value("sales_taxes",r['sales_taxes']);
	// 		// frm.set_value("purchase_taxes",r['purchase_taxes']);
	// 		frm.set_value("grand_total",r.docs[0].grand_total);
	// 		frm.refresh_field("sales_taxes");
	// 		frm.refresh_field("purchase_taxes");
	// 		frm.refresh_field("grand_total");
	// 		// console.log(r.docs[0].sales_taxes)
	// 		// frm.refresh();
	// 	}
	// })
	
}

function validate_conversion_rate(frm) {
	frm.doc.conversion_rate = flt(frm.doc.conversion_rate, (cur_frm) ? precision("conversion_rate") : 9);
	var conversion_rate_label = frappe.meta.get_label(frm.doc.doctype, "conversion_rate",
		frm.doc.name);
	// var company_currency = erpnext.get_company_currency();

	frm.set_value("conversion_rate", 1);
	// if(!frm.doc.conversion_rate) {
	// 	if(frm.doc.currency == company_currency) {
			
	// 	} else {
	// 		const subs =  [conversion_rate_label, frm.doc.currency, company_currency];
	// 		const err_message = __('{0} is mandatory. Maybe Currency Exchange record is not created for {1} to {2}', subs);
	// 		frappe.throw(err_message);
	// 	}
	// }
}


function calculate_item_values(frm) {
	let discount_amount_applied = false;
	let is_return=0;
	if (!discount_amount_applied) {
		$.each(frm.doc["items"] || [], function(i, item) {
			frappe.model.round_floats_in(item);
			item.net_rate = item.rate;
			
			// if ((!item.qty) && is_return) {
			// 	item.amount = flt(item.rate * 1, precision("amount", item));
			// }
			if (!item.qty) {
				item.amount = flt(item.rate * 1, precision("amount", item));
			}
			else{
				item.amount = flt(item.rate * item.qty, precision("amount", item));
			}
			item.net_amount = item.amount;
			item.item_tax_amount = 0.0;
			item.total_weight = flt(item.weight_per_unit * item.stock_qty);

			set_in_company_currency(frm,item, ["price_list_rate", "rate", "amount", "net_rate", "net_amount"]);
		});
	}

}

function initialize_taxes(frm) {
	let discount_amount_applied = false;
	$.each(frm.doc["taxes"] || [], function(i, tax) {
		tax.item_wise_tax_detail = {};
		var tax_fields = ["total", "tax_amount_after_discount_amount",
			"tax_amount_for_current_item", "grand_total_for_current_item",
			"tax_fraction_for_current_item", "grand_total_fraction_for_current_item"];

		if (cstr(tax.charge_type) != "Actual" &&
			!(discount_amount_applied && frm.doc.apply_discount_on=="Grand Total")) {
			tax_fields.push("tax_amount");
		}

		$.each(tax_fields, function(i, fieldname) { tax[fieldname] = 0.0; });

		if (!discount_amount_applied && cur_frm) {
			validate_taxes_and_charges(tax.doctype, tax.name);
			validate_inclusive_tax(tax);
		}
		frappe.model.round_floats_in(tax);
	});
}

function validate_taxes_and_charges(cdt, cdn) {
	var d = locals[cdt][cdn];
	var msg = "";

	if (d.account_head && !d.description) {
		// set description from account head
		d.description = d.account_head.split(' - ').slice(0, -1).join(' - ');
	}

	if (!d.charge_type && (d.row_id || d.rate || d.tax_amount)) {
		msg = __("Please select Charge Type first");
		d.row_id = "";
		d.rate = d.tax_amount = 0.0;
	} else if ((d.charge_type == 'Actual' || d.charge_type == 'On Net Total' || d.charge_type == 'On Paid Amount') && d.row_id) {
		msg = __("Can refer row only if the charge type is 'On Previous Row Amount' or 'Previous Row Total'");
		d.row_id = "";
	} else if ((d.charge_type == 'On Previous Row Amount' || d.charge_type == 'On Previous Row Total') && d.row_id) {
		if (d.idx == 1) {
			msg = __("Cannot select charge type as 'On Previous Row Amount' or 'On Previous Row Total' for first row");
			d.charge_type = '';
		} else if (!d.row_id) {
			msg = __("Please specify a valid Row ID for row {0} in table {1}", [d.idx, __(d.doctype)]);
			d.row_id = "";
		} else if (d.row_id && d.row_id >= d.idx) {
			msg = __("Cannot refer row number greater than or equal to current row number for this Charge type");
			d.row_id = "";
		}
	}
	if (msg) {
		frappe.validated = false;
		refresh_field("taxes");
		frappe.throw(msg);
	}

}


function validate_inclusive_tax(tax) {
	var actual_type_error = function() {
		var msg = __("Actual type tax cannot be included in Item rate in row {0}", [tax.idx])
		frappe.throw(msg);
	};

	var on_previous_row_error = function(row_range) {
		var msg = __("For row {0} in {1}. To include {2} in Item rate, rows {3} must also be included",
			[tax.idx, __(tax.doctype), tax.charge_type, row_range])
		frappe.throw(msg);
	};

	if(cint(tax.included_in_print_rate)) {
		if(tax.charge_type == "Actual") {
			// inclusive tax cannot be of type Actual
			actual_type_error();
		} else if(tax.charge_type == "On Previous Row Amount" &&
			!cint(frm.doc["taxes"][tax.row_id - 1].included_in_print_rate)
		) {
			// referred row should also be an inclusive tax
			on_previous_row_error(tax.row_id);
		} else if(tax.charge_type == "On Previous Row Total") {
			var taxes_not_included = $.map(frm.doc["taxes"].slice(0, tax.row_id),
				function(t) { return cint(t.included_in_print_rate) ? null : t; });
			if(taxes_not_included.length > 0) {
				// all rows above this tax should be inclusive
				on_previous_row_error(tax.row_id == 1 ? "1" : "1 - " + tax.row_id);
			}
		} else if(tax.category == "Valuation") {
			frappe.throw(__("Valuation type charges can not marked as Inclusive"));
		}
	}
}

function determine_exclusive_rate(frm) {
	let discount_amount_applied = false;
	var has_inclusive_tax = false;
	$.each(frm.doc["taxes"] || [], function(i, row) {
		if(cint(row.included_in_print_rate)) has_inclusive_tax = true;
	});
	if(has_inclusive_tax==false) return;

	$.each(frm.doc["items"] || [], function(n, item) {
		var item_tax_map = _load_item_tax_rate(item.item_tax_rate);
		var cumulated_tax_fraction = 0.0;
		var total_inclusive_tax_amount_per_qty = 0;
		$.each(frm.doc["taxes"] || [], function(i, tax) {
			var current_tax_fraction = get_current_tax_fraction(tax, item_tax_map);
			tax.tax_fraction_for_current_item = current_tax_fraction[0];
			var inclusive_tax_amount_per_qty = current_tax_fraction[1];

			if(i==0) {
				tax.grand_total_fraction_for_current_item = 1 + tax.tax_fraction_for_current_item;
			} else {
				tax.grand_total_fraction_for_current_item =
					frm.doc["taxes"][i-1].grand_total_fraction_for_current_item +
					tax.tax_fraction_for_current_item;
			}

			cumulated_tax_fraction += tax.tax_fraction_for_current_item;
			total_inclusive_tax_amount_per_qty += inclusive_tax_amount_per_qty * flt(item.qty);
		});

		if(!discount_amount_applied && item.qty && (total_inclusive_tax_amount_per_qty || cumulated_tax_fraction)) {
			var amount = flt(item.amount) - total_inclusive_tax_amount_per_qty;
			item.net_amount = flt(amount / (1 + cumulated_tax_fraction));
			item.net_rate = item.qty ? flt(item.net_amount / item.qty, precision("net_rate", item)) : 0;

			set_in_company_currency(frm,item, ["net_rate", "net_amount"]);
		}

		
	});

	
}
function get_current_tax_fraction(tax, item_tax_map){
	var current_tax_fraction = 0.0;
		var inclusive_tax_amount_per_qty = 0;

		if(cint(tax.included_in_print_rate)) {
			var tax_rate = _get_tax_rate(tax, item_tax_map);

			if(tax.charge_type == "On Net Total") {
				current_tax_fraction = (tax_rate / 100.0);

			} else if(tax.charge_type == "On Previous Row Amount") {
				current_tax_fraction = (tax_rate / 100.0) *
					this.frm.doc["taxes"][cint(tax.row_id) - 1].tax_fraction_for_current_item;

			} else if(tax.charge_type == "On Previous Row Total") {
				current_tax_fraction = (tax_rate / 100.0) *
					this.frm.doc["taxes"][cint(tax.row_id) - 1].grand_total_fraction_for_current_item;
			} else if (tax.charge_type == "On Item Quantity") {
				inclusive_tax_amount_per_qty = flt(tax_rate);
			}
		}

		if(tax.add_deduct_tax && tax.add_deduct_tax == "Deduct") {
			current_tax_fraction *= -1;
			inclusive_tax_amount_per_qty *= -1;
		}
		return [current_tax_fraction, inclusive_tax_amount_per_qty];
}

function _get_tax_rate(tax, item_tax_map) {
	return (Object.keys(item_tax_map).indexOf(tax.account_head) != -1) ?
		flt(item_tax_map[tax.account_head], precision("rate", tax)) : tax.rate;
}



function set_in_company_currency(frm,doc, fields) {
	$.each(fields, function(i, f) {
		doc["base_"+f] = flt(flt(doc[f], precision(f, doc)) * frm.doc.conversion_rate, precision("base_" + f, doc));
	});
}

function calculate_net_total(frm) {
	frm.doc.total_qty = frm.doc.total = frm.doc.base_total = frm.doc.net_total = frm.doc.base_net_total = 0.0;

	$.each(frm.doc["items"] || [], function(i, item) {
		frm.doc.total += item.amount;
		frm.doc.total_qty += item.qty;
		frm.doc.base_total += item.base_amount;
		frm.doc.net_total += item.net_amount;
		frm.doc.base_net_total += item.base_net_amount;
		});

	frappe.model.round_floats_in(frm.doc, ["total", "base_total", "net_total", "base_net_total"]);
}
function calculate_net_total(frm) {
	frm.doc.total_qty = frm.doc.total = frm.doc.base_total = frm.doc.net_total = frm.doc.base_net_total = 0.0;

	$.each(frm.doc["items"] || [], function(i, item) {
		frm.doc.total += item.amount;
		frm.doc.total_qty += item.qty;
		frm.doc.base_total += item.base_amount;
		frm.doc.net_total += item.net_amount;
		frm.doc.base_net_total += item.base_net_amount;
		});

	frappe.model.round_floats_in(frm.doc, ["total", "base_total", "net_total", "base_net_total"]);
}

function _load_item_tax_rate(item_tax_rate) {
	return item_tax_rate ? JSON.parse(item_tax_rate) : {};
}
function set_item_wise_tax(frm,item, tax, tax_rate, current_tax_amount) {
	// store tax breakup for each item
	let tax_detail = tax.item_wise_tax_detail;
	let key = item.item_code || item.item_name;

	if(typeof (tax_detail) == "string") {
		tax.item_wise_tax_detail = JSON.parse(tax.item_wise_tax_detail);
		tax_detail = tax.item_wise_tax_detail;
	}

	let item_wise_tax_amount = current_tax_amount * frm.doc.conversion_rate;
	if (tax_detail && tax_detail[key])
		item_wise_tax_amount += tax_detail[key][1];

	tax_detail[key] = [tax_rate, flt(item_wise_tax_amount, precision("base_tax_amount", tax))];
}

function _get_tax_rate(tax, item_tax_map) {
	return (Object.keys(item_tax_map).indexOf(tax.account_head) != -1) ?
		flt(item_tax_map[tax.account_head], precision("rate", tax)) : tax.rate;
}

function get_current_tax_amount(frm,item, tax, item_tax_map) {
	var tax_rate = _get_tax_rate(tax, item_tax_map);
	var current_tax_amount = 0.0;

	// To set row_id by default as previous row.
	if(["On Previous Row Amount", "On Previous Row Total"].includes(tax.charge_type)) {
		if (tax.idx === 1) {
			frappe.throw(
				__("Cannot select charge type as 'On Previous Row Amount' or 'On Previous Row Total' for first row"));
		}
		if (!tax.row_id) {
			tax.row_id = tax.idx - 1;
		}
	}
	if(tax.charge_type == "Actual") {
		// distribute the tax amount proportionally to each item row
		var actual = flt(tax.tax_amount, precision("tax_amount", tax));
		current_tax_amount = frm.doc.net_total ?
			((item.net_amount / frm.doc.net_total) * actual) : 0.0;

	} else if(tax.charge_type == "On Net Total") {
		current_tax_amount = (tax_rate / 100.0) * item.net_amount;
	} else if(tax.charge_type == "On Previous Row Amount") {
		current_tax_amount = (tax_rate / 100.0) *
			frm.doc["taxes"][cint(tax.row_id) - 1].tax_amount_for_current_item;

	} else if(tax.charge_type == "On Previous Row Total") {
		current_tax_amount = (tax_rate / 100.0) *
			frm.doc["taxes"][cint(tax.row_id) - 1].grand_total_for_current_item;
	} else if (tax.charge_type == "On Item Quantity") {
		current_tax_amount = tax_rate * item.qty;
	}

	set_item_wise_tax(frm,item, tax, tax_rate, current_tax_amount);

	return current_tax_amount;
}

function round_off_totals(tax) {
	if (frappe.flags.round_off_applicable_accounts.includes(tax.account_head)) {
		tax.tax_amount= Math.round(tax.tax_amount);
		tax.tax_amount_after_discount_amount = Math.round(tax.tax_amount_after_discount_amount);
	}

	tax.tax_amount = flt(tax.tax_amount, precision("tax_amount", tax));
	tax.tax_amount_after_discount_amount = flt(tax.tax_amount_after_discount_amount, precision("tax_amount", tax));
}
function set_in_company_currency(frm,doc, fields) {
	$.each(fields, function(i, f) {
		doc["base_"+f] = flt(flt(doc[f], precision(f, doc)) * frm.doc.conversion_rate, precision("base_" + f, doc));
	});
}

function round_off_base_values(tax) {
	if (frappe.flags.round_off_applicable_accounts.includes(tax.account_head)) {
		tax.base_tax_amount= Math.round(tax.base_tax_amount);
		tax.base_tax_amount_after_discount_amount = Math.round(tax.base_tax_amount_after_discount_amount);
	}
}

function set_cumulative_total(frm,row_idx, tax) {
	var tax_amount = tax.tax_amount_after_discount_amount;
	if (tax.category == 'Valuation') {
		tax_amount = 0;
	}

	if (tax.add_deduct_tax == "Deduct") { tax_amount = -1*tax_amount; }

	if(row_idx==0) {
		tax.total = flt(frm.doc.net_total + tax_amount, precision("total", tax));
	} else {
		tax.total = flt(frm.doc["taxes"][row_idx-1].total + tax_amount, precision("total", tax));
	}
}

function calculate_taxes(frm) {
	let discount_amount_applied = false;
	frm.doc.rounding_adjustment = 0;
	var actual_tax_dict = {};

	// maintain actual tax rate based on idx
	$.each(frm.doc["taxes"] || [], function(i, tax) {
		if (tax.charge_type == "Actual") {
			actual_tax_dict[tax.idx] = flt(tax.tax_amount, precision("tax_amount", tax));
		}
	});

	$.each(frm.doc["items"] || [], function(n, item) {
		var item_tax_map = _load_item_tax_rate(item.item_tax_rate);
		$.each(frm.doc["taxes"] || [], function(i, tax) {
			// tax_amount represents the amount of tax for the current step
			var current_tax_amount = get_current_tax_amount(frm,item, tax, item_tax_map);

			// Adjust divisional loss to the last item
			if (tax.charge_type == "Actual") {
				actual_tax_dict[tax.idx] -= current_tax_amount;
				if (n == frm.doc["items"].length - 1) {
					current_tax_amount += actual_tax_dict[tax.idx];
				}
			}

			// accumulate tax amount into tax.tax_amount
			if (tax.charge_type != "Actual" &&
				!(discount_amount_applied && frm.doc.apply_discount_on=="Grand Total")) {
				tax.tax_amount += current_tax_amount;
			}

			// store tax_amount for current item as it will be used for
			// charge type = 'On Previous Row Amount'
			tax.tax_amount_for_current_item = current_tax_amount;

			// tax amount after discount amount
			tax.tax_amount_after_discount_amount += current_tax_amount;

			// for buying
			if(tax.category) {
				// if just for valuation, do not add the tax amount in total
				// hence, setting it as 0 for further steps
				current_tax_amount = (tax.category == "Valuation") ? 0.0 : current_tax_amount;

				current_tax_amount *= (tax.add_deduct_tax == "Deduct") ? -1.0 : 1.0;
			}

			// note: grand_total_for_current_item contains the contribution of
			// item's amount, previously applied tax and the current tax on that item
			if(i==0) {
				tax.grand_total_for_current_item = flt(item.net_amount + current_tax_amount);
			} else {
				tax.grand_total_for_current_item =
					flt(frm.doc["taxes"][i-1].grand_total_for_current_item + current_tax_amount);
			}

			// set precision in the last item iteration
			if (n == frm.doc["items"].length - 1) {
				round_off_totals(tax);
				set_in_company_currency(frm,tax,
					["tax_amount", "tax_amount_after_discount_amount"]);

				round_off_base_values(tax);

				// in tax.total, accumulate grand total for each item
				set_cumulative_total(frm,i, tax);

				set_in_company_currency(frm,tax, ["total"]);

				// adjust Discount Amount loss in last tax iteration
				if ((i == frm.doc["taxes"].length - 1) && discount_amount_applied
					&& frm.doc.apply_discount_on == "Grand Total" && frm.doc.discount_amount) {
					frm.doc.rounding_adjustment = flt(frm.doc.grand_total -
						flt(frm.doc.discount_amount) - tax.total, precision("rounding_adjustment"));
				}
			}
		});
	});
}

function manipulate_grand_total_for_inclusive_tax(frm) {
	let discount_amount_applied = false;
	// if fully inclusive taxes and diff
	if (frm.doc["taxes"] && frm.doc["taxes"].length) {
		var any_inclusive_tax = false;
		$.each(frm.doc.taxes || [], function(i, d) {
			if(cint(d.included_in_print_rate)) any_inclusive_tax = true;
		});
		if (any_inclusive_tax) {
			var last_tax = frm.doc["taxes"].slice(-1)[0];
			var non_inclusive_tax_amount = frappe.utils.sum($.map(frm.doc.taxes || [],
				function(d) {
					if(!d.included_in_print_rate) {
						return flt(d.tax_amount_after_discount_amount);
					}
				}
			));
			var diff = frm.doc.total + non_inclusive_tax_amount
				- flt(last_tax.total, precision("grand_total"));

			if(discount_amount_applied && frm.doc.discount_amount) {
				diff -= flt(frm.doc.discount_amount);
			}

			diff = flt(diff, precision("rounding_adjustment"));

			if ( diff && Math.abs(diff) <= (5.0 / Math.pow(10, precision("tax_amount", last_tax))) ) {
				frm.doc.rounding_adjustment = diff;
			}
		}
	}
}
function calculate_totals(frm) {
	// Changing sequence can cause rounding_adjustmentng issue and on-screen discrepency
	var tax_count = frm.doc["taxes"] ? frm.doc["taxes"].length : 0;
	frm.doc.grand_total = flt(tax_count
		? frm.doc["taxes"][tax_count - 1].total + flt(frm.doc.rounding_adjustment)
		: frm.doc.net_total);

	if(in_list(["Quotation", "Sales Order", "Delivery Note", "Sales Invoice", "POS Invoice","Credit and Debit Note"], frm.doc.doctype)) {
		frm.doc.base_grand_total = (frm.doc.total_taxes_and_charges) ?
			flt(frm.doc.grand_total * frm.doc.conversion_rate) : frm.doc.base_net_total;
	} else {
		// other charges added/deducted
		frm.doc.taxes_and_charges_added = frm.doc.taxes_and_charges_deducted = 0.0;
		if(tax_count) {
			$.each(frm.doc["taxes"] || [], function(i, tax) {
				if (in_list(["Valuation and Total", "Total"], tax.category)) {
					if(tax.add_deduct_tax == "Add") {
						frm.doc.taxes_and_charges_added += flt(tax.tax_amount_after_discount_amount);
					} else {
						frm.doc.taxes_and_charges_deducted += flt(tax.tax_amount_after_discount_amount);
					}
				}
			});

			frappe.model.round_floats_in(frm.doc,
				["taxes_and_charges_added", "taxes_and_charges_deducted"]);
		}

		frm.doc.base_grand_total = flt((frm.doc.taxes_and_charges_added || frm.doc.taxes_and_charges_deducted) ?
			flt(frm.doc.grand_total * frm.doc.conversion_rate) : frm.doc.base_net_total);

		set_in_company_currency(frm,frm.doc,
			["taxes_and_charges_added", "taxes_and_charges_deducted"]);
	}

	frm.doc.total_taxes_and_charges = flt(frm.doc.grand_total - frm.doc.net_total
		- flt(frm.doc.rounding_adjustment), precision("total_taxes_and_charges"));

	set_in_company_currency(frm,frm.doc, ["total_taxes_and_charges", "rounding_adjustment"]);

	// Round grand total as per precision
	frappe.model.round_floats_in(frm.doc, ["grand_total", "base_grand_total"]);

	// rounded totals
	set_rounded_total(frm);
}
function set_rounded_total(frm) {
	var disable_rounded_total = 0;
	if(frappe.meta.get_docfield(frm.doc.doctype, "disable_rounded_total", frm.doc.name)) {
		disable_rounded_total = frm.doc.disable_rounded_total;
	} else if (frappe.sys_defaults.disable_rounded_total) {
		disable_rounded_total = frappe.sys_defaults.disable_rounded_total;
	}

	if (cint(disable_rounded_total)) {
		frm.doc.rounded_total = 0;
		frm.doc.base_rounded_total = 0;
		return;
	}

	if(frappe.meta.get_docfield(frm.doc.doctype, "rounded_total", frm.doc.name)) {
		frm.doc.rounded_total = round_based_on_smallest_currency_fraction(frm.doc.grand_total,
			frm.doc.currency, precision("rounded_total"));
		frm.doc.rounding_adjustment += flt(frm.doc.rounded_total - frm.doc.grand_total,
			precision("rounding_adjustment"));

		set_in_company_currency(frm,frm.doc, ["rounding_adjustment", "rounded_total"]);
	}
}
function _cleanup(frm) {
	frm.doc.base_in_words = frm.doc.in_words = "";

	if(frm.doc["items"] && frm.doc["items"].length) {
		if(!frappe.meta.get_docfield(frm.doc["items"][0].doctype, "item_tax_amount", frm.doctype)) {
			$.each(frm.doc["items"] || [], function(i, item) {
				delete item["item_tax_amount"];
			});
		}
	}
	if(frm.doc["taxes"] && frm.doc["taxes"].length) {
		var temporary_fields = ["tax_amount_for_current_item", "grand_total_for_current_item",
			"tax_fraction_for_current_item", "grand_total_fraction_for_current_item"];

		if(!frappe.meta.get_docfield(frm.doc["taxes"][0].doctype, "tax_amount_after_discount_amount", frm.doctype)) {
			temporary_fields.push("tax_amount_after_discount_amount");
		}

		$.each(frm.doc["taxes"] || [], function(i, tax) {
			$.each(temporary_fields, function(i, fieldname) {
				delete tax[fieldname];
			});

			tax.item_wise_tax_detail = JSON.stringify(tax.item_wise_tax_detail);
		});
	}
}

