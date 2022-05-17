import frappe
from frappe.modules.export_file import export_to_files
from frappe.desk.doctype.form_tour.form_tour import FormTour

def before_save(self,methord):
	meta = frappe.get_meta(self.reference_doctype)
	for step in self.steps:
		if step.get('is_table_field',None) and step.GET('parent_fieldname',None):
			parent_field_df = meta.get_field(step.parent_fieldname)
			step.child_doctype = parent_field_df.options

			field_df = frappe.get_meta(step.child_doctype).get_field(step.fieldname)
			step.label = field_df.label
			step.fieldtype = field_df.fieldtype
		else:
			field_df = meta.get_field(step.fieldname)
			step.label = field_df.label
			step.fieldtype = field_df.fieldtype

def on_update(self,methord):
	if frappe.conf.developer_mode and self.get('is_standard'):
		export_to_files([["Form Tour", self.name]], self.module)

