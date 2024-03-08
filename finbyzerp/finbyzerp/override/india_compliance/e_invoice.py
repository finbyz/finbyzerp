import frappe
import base64
import os

from frappe.integrations.utils import make_request
from frappe.utils.password import get_decrypted_password
from frappe.utils.data import add_to_date, time_diff_in_seconds
from frappe.utils import now_datetime

def get_auth_token(self):
	if not hasattr(self, 'gst_settings'):
		self.gst_settings = frappe.get_cached_doc("GST Settings")
	if time_diff_in_seconds(self.gst_settings.token_expiry, now_datetime()) < 150.0 or not self.gst_settings.auth_token:
		fetch_auth_token(self)

	return self.gst_settings.auth_token
	
def get_client_details(self):
	if self.gst_settings.get('client_id') and self.gst_settings.get('client_secret'):
		return self.gst_settings.get('client_id'), get_decrypted_password("GST Settings", "GST Settings", fieldname = "client_secret")

	return frappe.conf.einvoice_client_id, frappe.conf.einvoice_client_secret

def fetch_auth_token(self):
	client_id, client_secret = get_client_details(self)
	headers = {"gspappid": client_id, "gspappsecret": client_secret}
	res = {}
	url = "https://gsp.adaequare.com/gsp/authenticate?grant_type=token"
	res = make_request("post", url, headers = headers)
	self.gst_settings.auth_token = "{} {}".format(
		res.get("token_type"), res.get("access_token")
	)
	self.gst_settings.token_expiry = add_to_date(None, seconds=res.get("expires_in"))
	self.gst_settings.save(ignore_permissions=True)
	self.gst_settings.reload()


def einvoice_setup(self, doc=None, *, company_gstin=None):
	self.BASE_PATH = "enriched/ei/api"
	if not self.settings.enable_e_invoice:
		frappe.throw(_("Please enable e-Waybill features in GST Settings first"))
	self.gst_settings = frappe.get_cached_doc("GST Settings")
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
			"user_name": self.username,
			"password": self.password,
			"requestid": str(base64.b64encode(os.urandom(18))),
		}
	)