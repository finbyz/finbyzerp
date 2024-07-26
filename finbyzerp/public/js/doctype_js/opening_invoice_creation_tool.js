frappe.ui.form.on('Opening Invoice Creation Tool Item',{
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
