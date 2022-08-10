frappe.ui.form.on('Role Profile', {
	refresh: function(frm) {
		if (has_common(frappe.user_roles, ["Administrator", "System Manager", "Local Admin"])) {
			if (!frm.roles_editor) {
				const role_area = $(frm.fields_dict.roles_html.wrapper);
				frm.roles_editor = new frappe.RoleEditor(role_area, frm);
			}
			frm.roles_editor.show();

		}
	},
});
