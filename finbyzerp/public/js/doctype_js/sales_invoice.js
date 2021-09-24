frappe.ui.form.on('Sales Invoice', {
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
		if (frappe.meta.get_docfield("Sales Invoice", "series_value", frm.doc.name)){
			if (frm.doc.__islocal && frm.doc.company && !frm.doc.amended_from) {
				frappe.call({
					method: "finbyzerp.api.check_counter_series",
					args: {
						'name': frm.doc.naming_series,
						'company_series': frm.doc.company_series || null,
						'date': frm.doc.posting_date,
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
	posting_date: function (frm) {
		frm.trigger('naming_series');
	},
	validate:function(frm){
		if(frm.doc.customer_address && !frm.doc.shipping_address_name){
			frappe.model.set_value("Sales invoice",frm.doc.name,"shipping_address_name",frm.doc.customer_address)
			frm.refresh();
			
		}
	}

});