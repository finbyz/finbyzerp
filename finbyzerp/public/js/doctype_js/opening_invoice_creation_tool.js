frappe.ui.form.on("Opening Invoice Creation Tool", {
	update_invoice_table_td: function (frm) {
		

		const child_meta = frappe.get_meta("Opening Invoice Creation Tool Item");

		// dimension fields = fields having depends_on like accounting_dimension
		const dimension_fields = child_meta.fields.filter(df =>
			df.fieldtype === "Link" &&
			df.options &&
			df.fieldname !== "cost_center" &&   // optional
			frm.doc.hasOwnProperty(df.fieldname)
		);

		(frm.doc.invoices || []).forEach(row => {
			dimension_fields.forEach(df => {
				if (frm.doc[df.fieldname]) {
					row[df.fieldname] = frm.doc[df.fieldname];
				}
			});
		});

		frm.refresh_field("invoices");
	

		
	},
});


frappe.ui.form.on('Opening Invoice Creation Tool Item',{
    invoices_add: function (frm) {
		frm.trigger("update_invoice_table_td");
	},
    party: function(frm,cdt,cdn){
        var row = locals[cdt][cdn];
        if (frm.doc.invoices && frm.doc.invoice_type){
                if(row.party){
                    frappe.call({
                        method:"finbyzerp.finbyzerp.override.doctype.opening_invoice_creation_tool.get_account_currency",
                        args:{
                            "party":row.party,
                            "company":frm.doc.company,
                            "invoice_type":frm.doc.invoice_type
                        },
                        callback: function(r){
                            if (r.message){
                                frappe.model.set_value(row.doctype,row.name,'account',r.message.account)
                                frappe.model.set_value(row.doctype,row.name,'currency',r.message.currency)
                            }
                        }
                    })
                }
        }
    }
})



