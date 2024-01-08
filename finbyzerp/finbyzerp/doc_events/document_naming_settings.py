import frappe
from frappe.core.doctype.document_naming_settings.document_naming_settings import DocumentNamingSettings
from frappe.model.naming import NamingSeries
from frappe import _

class CustomDocumentNamingSettings(DocumentNamingSettings):
	@frappe.whitelist()
	def update_series_start(self):
		frappe.only_for(("System Manager", "Local Admin"))

		if self.prefix is None:
			frappe.throw(_("Please select prefix first"))

		naming_series = NamingSeries(self.prefix)
		previous_value = naming_series.get_current_value()
		naming_series.update_counter(self.current_value)

		self.create_version_log_for_change(
			naming_series.get_prefix(), previous_value, self.current_value
		)

		frappe.msgprint(
			_("Series counter for {} updated to {} successfully").format(self.prefix, self.current_value),
			alert=True,
			indicator="green",
		)