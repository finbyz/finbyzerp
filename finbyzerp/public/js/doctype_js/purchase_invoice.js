frappe.ui.form.on('Purchase Invoice', {
	refresh: (frm) => {
		if (frm.doc.__islocal){
		frm.set_df_property("company", "read_only", (!frm.doc.__islocal || frm.doc.amended_from) ? 1 : 0);
		}
	},
	onload: (frm) => {
		if (frm.doc.__islocal){
		frm.trigger('naming_series');
		}
	},
	billing_address: function(frm) {
		// frappe.msgprint("hello")
		if(cur_frm.doc.billing_address) {
			return frappe.call({
				method: "frappe.contacts.doctype.address.address.get_address_display",
				args: {
					"address_dict": frm.doc.billing_address
				},
				callback: function(r) {
					if(r.message){
						frm.set_value("billing_address_display", r.message);
					}
				}
			});
		}
	},

	posting_date: function (frm) {
		frm.trigger('naming_series');
	},
	naming_series: function (frm) {
		if (frappe.meta.get_docfield("Purchase Invoice", "series_value", frm.doc.name)){
			if (frm.doc.__islocal && frm.doc.company && !frm.doc.amended_from) {
				frappe.call({
					method: "finbyzerp.api.check_counter_series",
					args: {
						'name': frm.doc.naming_series,
						'date': frm.doc.posting_date,
						'company_series': frm.doc.company_series || null,
					},
					callback: function (e) {
						// frm.doc.series_value = e.message;
						frm.set_value('series_value', e.message);

					}
				});
				// frm.refresh_field('series_value')
			}
		}
	},
	company: function (frm) {
		frm.trigger('naming_series');
	},
	transaction_date: function (frm) {
		frm.trigger('naming_series');
	},
});