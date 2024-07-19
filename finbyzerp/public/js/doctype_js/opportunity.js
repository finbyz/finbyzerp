frappe.ui.form.on('Opportunity', {
	status: function(frm) {
		if (frm.doc.status== "Not Interested" || frm.doc.status== "Do Not Contact" ){
			frm.set_value("contact_by", "");
			frm.set_value("contact_date", "");
		}
	}
});
