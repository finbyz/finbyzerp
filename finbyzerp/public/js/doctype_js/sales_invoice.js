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
		if (frm.doc.irn_cancelled && frm.doc.irn && frm.doc.__islocal && frm.doc.amended_from){
            frm.set_value("irn",'')
            frm.set_value("irn_cancelled",0)
        }
        if (frm.doc.eway_bill_cancelled && frm.doc.ewaybill && frm.doc.__islocal && frm.doc.amended_from){
            frm.set_value("ewaybill",'')
            frm.set_value("eway_bill_cancelled",0)
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