frappe.ui.form.on('Sales Order', {
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
	naming_series: function (frm) {
		if (frappe.meta.get_docfield("Sales Order", "series_value", frm.doc.name)){
			if (frm.doc.__islocal && frm.doc.company && !frm.doc.amended_from) {
				frappe.call({
					method: "finbyzerp.api.check_counter_series",
					args: {
						'name': frm.doc.naming_series,
						'date': frm.doc.transaction_date,
						'company_series': frm.doc.company_series || null,
					},
					callback: function (e) {
						// frm.doc.series_value = e.message;
						frm.set_value('series_value', e.message);

					}
				});
			}
		}
	},
	company: function (frm) {
		frm.trigger('naming_series');
	},
	transaction_date: function (frm) {
		frm.trigger('naming_series');
		frm.trigger('payment_terms_template');
	},
	payment_terms_template: function (frm) {
		if (frm.doc.payment_terms_template) {
			frappe.call({
				method: "erpnext.controllers.accounts_controller.get_payment_terms",
				args: {
					'terms_template' : frm.doc.payment_terms_template
				},
				callback: function (e) {
					frm.set_value('payment_schedule', e.message);
				}
			});
		}
	},
});

cur_frm.fields_dict.other_contacts.grid.get_field("contact").get_query = function(doc) {
	if(cur_frm.doc.customer) {
		return {
			query: "frappe.contacts.doctype.contact.contact.contact_query",
			filters: { link_doctype: "Customer", link_name: cur_frm.doc.customer} 
		};
	}
	else frappe.throw(__("Please set Customer"));
};

frappe.ui.form.on('Other Contact', {

});