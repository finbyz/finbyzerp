frappe.ui.form.on('Payment Entry', {
	refresh: (frm) => {
		if (frm.doc.__islocal){
			frm.set_df_property("company", "read_only", (!frm.doc.__islocal || frm.doc.amended_from) ? 1 : 0);
		}
	},
	onload: (frm) => {
		if (frm.doc.__islocal){
		frm.trigger('naming_series');
		}
		cur_frm.set_query("address", function (doc) {
			return {
				query: "frappe.contacts.doctype.address.address.address_query",
				filters: { link_doctype: doc.party_type, link_name: doc.party }
			};
		})
		frm.trigger('set_address');
	},
	before_save: function(frm){
		frm.trigger('set_address');
	},
	party: function(frm){
		if(	in_list(["Customer", "Supplier"], (frm.doc.party_type)) && frm.doc.party){
			if (frappe.meta.get_docfield("Payment Entry", "address", frm.doc.name)){
				frappe.call({
					method:"erpnext.accounts.party.get_party_details",
					args:{
						party: frm.doc.party,
						party_type: frm.doc.party_type
					},
					callback: function(r){
						if(r.message){
							var adrr = frappe.scrub(frm.doc.party_type) + "_address"
							if(frm.doc.address != r.message[adrr]){
								frm.set_value('address', r.message[adrr])
							}
						}
					}
				})
			}
		}
	},
	validate: function(frm) {
		
		if(!frm.doc.address){
			if(	in_list(["Customer", "Supplier"], (frm.doc.party_type)) && frm.doc.party){
				if (frappe.meta.get_docfield("Payment Entry", "address", frm.doc.name)){
					frappe.call({
						method:"erpnext.accounts.party.get_party_details",
						args:{
							party: frm.doc.party,
							party_type: frm.doc.party_type
						},
						callback: function(r){
							if(r.message){
								var adrr = frappe.scrub(frm.doc.party_type) + "_address"
								if(frm.doc.address != r.message[adrr]){
									frm.set_value('address', r.message[adrr])
								}
							}
							frm.refresh();
						}
					})
			}
			}
		}
	},
	naming_series: function (frm) {
		if (frappe.meta.get_docfield("Payment Entry", "series_value", frm.doc.name)){
			if (frm.doc.__islocal && frm.doc.company && !frm.doc.amended_from) {
				frappe.call({
					method: "finbyzerp.api.check_counter_series",
					args: {
						'name': frm.doc.naming_series,
						'date': frm.doc.transaction_date,
						'company_series': frm.doc.company_series || null,
					},
					callback: function (e) {
						frm.set_value('series_value', e.message);
						// frm.doc.series_value = e.message;
					}
				});
				
			}
		}
	},
	company: function (frm) {
		frm.trigger('naming_series');
	},
	posting_date: function (frm) {
		frm.trigger('naming_series');
	},
	
});


frappe.ui.form.on('Payment Entry Reference', {
	unallocate_payment: function(frm,cdt,cdn){
		let d = locals[cdt][cdn];
		if (frm.doc.docstatus == 1){
			frappe.call({
				method:"finbyzerp.finbyzerp.doc_events.payment_entry.unallocate_payment",
				args:{
					"child_doc_name":d.name,
					"parent_doc_name":frm.doc.name,
					"reference_doctype":d.reference_doctype,
					"reference_name":d.reference_name
				},
				callback: function(r){
					if (r.message){
						// frm.refresh_fields();
						frappe.msgprint(r.message)
					}
				}
			})
		}
	}
});

cur_frm.fields_dict.other_contacts.grid.get_field("contact").get_query = function(doc) {
	if(cur_frm.doc.party_name) {
		return {
			query: "frappe.contacts.doctype.contact.contact.contact_query",
			filters: { link_doctype: cur_frm.doc.party_type, link_name: cur_frm.doc.party_name} 
		};
	}
	else frappe.throw(__("Please set Party"));
};

frappe.ui.form.on('Other Contact', {

});