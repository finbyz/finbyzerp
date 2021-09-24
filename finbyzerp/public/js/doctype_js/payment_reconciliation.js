frappe.ui.form.on("Payment Reconciliation", {
    refresh: function(frm){
        var prev_route = frappe.get_prev_route()
        if (prev_route[0] == "Form" && prev_route[1] == "Credit and Debit Note" && prev_route[2]){
            frappe.db.get_value("Credit and Debit Note",prev_route[2],["company","party_type","party","posting_date"], function(r){
                frm.set_value('company',r.company)
                frm.set_value('from_date',r.posting_date)
                frm.set_value('to_date',r.posting_date)
                frm.set_value('party_type',r.party_type)
                frm.set_value('party',r.party)
                frm.set_value('payments',[])
            })
        }    
    },
})