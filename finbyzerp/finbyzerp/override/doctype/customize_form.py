import frappe
import os
from frappe.utils import cint
from frappe import get_module_path, scrub
from india_compliance.audit_trail.overrides.customize_form import CustomizeForm as _CustomizeForm
from frappe.model import core_doctypes_list
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import delete_property_setter
import json


class CustomizeForm(_CustomizeForm):
	def validate_doctype(self, meta):
		"""
		Check if the doctype is allowed to be customized.
		"""
		if self.doc_type in core_doctypes_list:
			frappe.throw(_("Core DocTypes cannot be customized."))

		# if meta.issingle:
		# 	frappe.throw(_("Single DocTypes cannot be customized."))

		if meta.custom:
			frappe.throw(_("Only standard DocTypes are allowed to be customized from Customize Form."))

@frappe.whitelist()
def export_customizations(
	module: str, doctype: str, sync_on_migrate: bool = False, with_permissions: bool = False
):
	"""Export Custom Field and Property Setter for the current document to the app folder.
	This will be synced with bench migrate"""

	sync_on_migrate = cint(sync_on_migrate)
	with_permissions = cint(with_permissions)

	if not frappe.conf.developer_mode:
		frappe.throw(_("Only allowed to export customizations in developer mode"))

	custom = {
		"custom_fields": frappe.get_all("Custom Field", fields="*", filters={"dt": doctype,"module":module}),
		"property_setters": frappe.get_all("Property Setter", fields="*", filters={"doc_type": doctype,"module":module}),
		"custom_perms": [],
		"links": frappe.get_all("DocType Link", fields="*", filters={"parent": doctype}),
		"doctype": doctype,
		"sync_on_migrate": sync_on_migrate,
	}

	if with_permissions:
		custom["custom_perms"] = frappe.get_all("Custom DocPerm", fields="*", filters={"parent": doctype})

	# also update the custom fields and property setters for all child tables
	for d in frappe.get_meta(doctype).get_table_fields():
		export_customizations(module, d.options, sync_on_migrate, with_permissions)

	if custom["custom_fields"] or custom["property_setters"] or custom["custom_perms"]:
		folder_path = os.path.join(get_module_path(module), "custom")
		if not os.path.exists(folder_path):
			os.makedirs(folder_path)

		path = os.path.join(folder_path, scrub(doctype) + ".json")
		with open(path, "w") as f:
			f.write(frappe.as_json(custom))

		frappe.msgprint(_("Customizations for <b>{0}</b> exported to:<br>{1}").format(doctype, path))
		return path

