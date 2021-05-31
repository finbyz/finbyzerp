frappe.ui.form.on('Stock Entry', {
	refresh: (frm) => {
		if (frm.doc.__islocal){
		frm.set_df_property("company", "read_only", (!frm.doc.__islocal || frm.doc.amended_from) ? 1 : 0);
	
		}
	},
	onload: (frm) => {
		if (frm.doc.__islocal){
			if (frm.doc.company){
				frappe.call({
					method: 'frappe.client.get_value',
					args: {
					  doctype: 'Company',
					  filters: {
						'name': frm.doc.company,
					  },
					  fieldname: ['company_series']
					},
					callback: function (r) {
						frm.set_value('company_series',r.message.company_series)
					}
			})
			frm.trigger('change_series_value');
			}
		}
	},
	change_series_value: function (frm) {
		if (frappe.meta.get_docfield("Stock Entry", "series_value", frm.doc.name)){
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
	naming_series: function (frm) {
		frm.trigger('change_series_value');
	},
	company: function (frm) {
		frm.trigger('change_series_value');
	},
	posting_date: function (frm) {
		frm.trigger('change_series_value');
	},
});