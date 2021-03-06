frappe.ui.form.on('GST Settings', {
	setup: function(frm) {
		$.each(["tcs_account"], function(i, field) {
			frm.events.filter_accounts(frm, field);
		});
	},

	filter_accounts: function(frm, account_field) {
		frm.set_query(account_field, "gst_accounts", function(doc, cdt, cdn) {
			var row = locals[cdt][cdn];
			return {
				filters: {
					company: row.company,
					is_group: 0
				}
			};
		});
	}
})