frappe.views.ListView = class ListView extends frappe.views.ListView {
	get_menu_items() {
		const doctype = this.doctype;
		const items = [];

		if (frappe.model.can_import(doctype, null, this.meta)) {
			items.push({
				label: __("Import", null, "Button in list view menu"),
				action: () =>
					frappe.set_route("list", "data-import", {
						reference_doctype: doctype,
					}),
				standard: true,
			});
		}

		if (frappe.user_roles.includes("System Manager")) {
			items.push({
				label: __("User Permissions", null, "Button in list view menu"),
				action: () =>
					frappe.set_route("list", "user-permission", {
						allow: doctype,
					}),
				standard: true,
			});
		}

		if (frappe.user_roles.includes("System Manager")) {
			items.push({
				label: __("Role Permissions Manager", null, "Button in list view menu"),
				action: () =>
					frappe.set_route("permission-manager", {
						doctype,
					}),
				standard: true,
			});
		}

		if (
			frappe.model.can_create("Custom Field") &&
			frappe.model.can_create("Property Setter") &&
			frappe.session.user == "Administrator"
		) {
			items.push({
				label: __("Customize", null, "Button in list view menu"),
				action: () => {
					if (!this.meta) return;
					if (this.meta.custom) {
						frappe.set_route("form", "doctype", doctype);
					} else if (!this.meta.custom) {
						frappe.set_route("form", "customize-form", {
							doc_type: doctype,
						});
					}
				},
				standard: true,
				shortcut: "Ctrl+J",
			});
		}

		items.push({
			label: __("Toggle Sidebar", null, "Button in list view menu"),
			action: () => this.toggle_side_bar(),
			condition: () => !this.hide_sidebar,
			standard: true,
			shortcut: "Ctrl+K",
		});

		if (frappe.user.has_role("System Manager") && frappe.boot.developer_mode === 1 && frappe.session.user == "Administrator") {
			// edit doctype
			items.push({
				label: __("Edit DocType", null, "Button in list view menu"),
				action: () => frappe.set_route("form", "doctype", doctype),
				standard: true,
			});
		}

		if (frappe.user.has_role("System Manager")) {
			if (this.get_view_settings) {
				items.push(this.get_view_settings());
			}
		}

		return items;
	}
}