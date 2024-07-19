import frappe
from frappe import _
from frappe.integrations.utils import make_request
from frappe.utils.password import get_decrypted_password
from frappe.utils.data import add_to_date, time_diff_in_seconds
from frappe.utils import now_datetime
from india_compliance.gst_india.api_classes.base import check_scheduler_status

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


def setup(self, doc=None, *, company_gstin=None):
	self.BASE_PATH = "enriched/ei/api"
	self.gst_settings = frappe.get_cached_doc("GST Settings")

	if not self.settings.enable_e_invoice:
		frappe.throw(_("Please enable e-Invoicing in GST Settings first"))

	check_scheduler_status()

	if doc:
		company_gstin = doc.company_gstin
		self.default_log_values.update(
			reference_doctype=doc.doctype,
			reference_name=doc.name,
		)

	if self.sandbox_mode:
		company_gstin = "02AMBPG7773M002"
		self.username = "adqgsphpusr1"
		self.password = "Gsp@1234"

	elif not company_gstin:
		frappe.throw(_("Company GSTIN is required to use the e-Invoice API"))

	else:
		self.fetch_credentials(company_gstin, "e-Waybill / e-Invoice")

	self.default_headers.update(
		{
			"authorization": get_auth_token(self),
			"gstin": company_gstin,
			"user_name": self.username,
			"password": self.password,
			"requestid": self.generate_request_id(),
		}
	)
