frappe.ui.form.on("Fiscal Year", {
	before_save: function(frm){
		let start_year = frm.doc.year_start_date.split("-")[0].slice(2);
		let end_year = frm.doc.year_end_date.split("-")[0].slice(2);

		let fiscal = start_year + end_year;
		frm.set_value("fiscal", fiscal);
	}
});