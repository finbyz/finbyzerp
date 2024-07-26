import frappe
import os
import json
from frappe.utils import cint
from frappe import _
from frappe import get_module_path, scrub
from india_compliance.audit_trail.overrides.customize_form import CustomizeForm as _CustomizeForm
from frappe.custom.doctype.property_setter.property_setter import delete_property_setter

class CustomizeForm(_CustomizeForm):
	def set_property_setter_for_field_order(self, meta):
		new_order = [df.fieldname for df in self.fields]

		doc_list = frappe.get_list("Field Sequence", pluck='doc_type')

		if self.doc_type in doc_list:
			field_names = frappe.db.get_list("Field Sequence Table", filters={'doc_type': self.doc_type}, fields=['field_name', 'idx'])
			sorted_fields = sorted(field_names, key=lambda x: x['idx'])

			# Remove multiple fields
			fields_to_remove = [field['field_name'] for field in sorted_fields]
			
			new_order = [field for field in new_order if field not in fields_to_remove]

			# Get the index of the standard field "section_break_31"
			sbi = frappe.db.get_value('Field Sequence', {'doc_type': self.doc_type}, ['add_fields_before_section'])
			section_break_index = new_order.index(sbi)

			# Append multiple fields before the standard field "section_break"
			fields_to_append = fields_to_remove
			new_order = new_order[:section_break_index] + fields_to_append + new_order[section_break_index:]

			existing_order = getattr(meta, "field_order", None)
			default_order = [
				fieldname for fieldname, df in meta._fields.items() if not getattr(df, "is_custom_field", False)
			]

			field_order_doc = frappe.db.get_value('Field Order', {'doc_type': self.doc_type}, ['name'])
			if field_order_doc:
				upd_field_order = frappe.get_doc('Field Order', field_order_doc)
				upd_field_order.field_order_list = json.dumps(new_order)
				upd_field_order.save(ignore_permissions=True)
			else:
				new_field_order = frappe.new_doc('Field Order')
				new_field_order.doc_type = self.doc_type
				new_field_order.field_order_list = json.dumps(new_order)
				new_field_order.save(ignore_permissions=True)

			if new_order == default_order:
				if existing_order:
					pass
					# delete_property_setter(self.doc_type, "field_order")

				return

			if existing_order and new_order == json.loads(existing_order):
				return

			frappe.make_property_setter(
				{
					"doctype": self.doc_type,
					"doctype_or_field": "DocType",
					"property": "field_order",
					"value": json.dumps(new_order),
				},
				is_system_generated=True,
			)
		else:
			existing_order = getattr(meta, "field_order", None)
			default_order = [
				fieldname for fieldname, df in meta._fields.items() if not getattr(df, "is_custom_field", False)
			]

			if new_order == default_order:
				if existing_order:
					delete_property_setter(self.doc_type, "field_order")

				return

			if existing_order and new_order == json.loads(existing_order):
				return

			frappe.make_property_setter(
				{
					"doctype": self.doc_type,
					"doctype_or_field": "DocType",
					"property": "field_order",
					"value": json.dumps(new_order),
				},
				is_system_generated=True,
			)
@frappe.whitelist()
def export_customizations(module, doctype, sync_on_migrate=0, with_permissions=0):
	"""Export Custom Field and Property Setter for the current document to the app folder.
	This will be synced with bench migrate"""

	sync_on_migrate = cint(sync_on_migrate)
	with_permissions = cint(with_permissions)

	if not frappe.get_conf().developer_mode:
		raise Exception("Not developer mode")

	custom = {
		"custom_fields": [],
		"property_setters": [],
		"custom_perms": [],
		"links": [],
		"doctype": doctype,
		"sync_on_migrate": sync_on_migrate,
	}

	def add(_doctype):
		custom["custom_fields"] += frappe.get_all("Custom Field", fields="*", filters={"dt": _doctype, "module":module})
		custom["property_setters"] += frappe.get_all(
			"Property Setter", fields="*", filters={"doc_type": _doctype, "module":module}
		)
		custom["links"] += frappe.get_all("DocType Link", fields="*", filters={"parent": _doctype})

	add(doctype)

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

