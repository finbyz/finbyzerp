import frappe
import base64
import os

from finbyzerp.finbyzerp.override.india_compliance.e_invoice import get_auth_token

def ewaybill_setup(self, doc=None, *, company_gstin=None):
	self.gst_settings = frappe.get_cached_doc("GST Settings")
	self.BASE_PATH = "enriched/ewb/ewayapi"
	if not self.settings.enable_e_waybill:
		frappe.throw(_("Please enable e-Waybill features in GST Settings first"))

	if doc:
		company_gstin = doc.company_gstin
		self.default_log_values.update(
			reference_doctype=doc.doctype,
			reference_name=doc.name,
		)

	if self.sandbox_mode:
		company_gstin = "05AAACG2115R1ZN"
		self.username = "05AAACG2115R1ZN"
		self.password = "abc123@@"

	elif not company_gstin:
		frappe.throw(_("Company GSTIN is required to use the e-Waybill API"))

	else:
		self.fetch_credentials(company_gstin, "e-Waybill / e-Invoice")

	self.default_headers.update(
		{
			"authorization": get_auth_token(self),
			"gstin": company_gstin,
			"username": self.username,
			"password": self.password,
			"requestid": str(base64.b64encode(os.urandom(18))),
		}
	)