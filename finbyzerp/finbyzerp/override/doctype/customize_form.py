import frappe
from frappe import _
from frappe.custom.doctype.customize_form.customize_form import CustomizeForm
from frappe.model import core_doctypes_list


class CustomCustomizeForm(CustomizeForm):
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