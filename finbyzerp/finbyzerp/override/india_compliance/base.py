import frappe
from frappe import _
from urllib.parse import urljoin
from india_compliance.exceptions import GatewayTimeoutError

BASE_URL = "https://gsp.adaequare.com"

def get_url(self, *parts):
	parts = list(parts)

	# If the first part is a URL, return it as it is
	if parts and parts[0].startswith("https"):
		return parts[0]
	
	if not parts[-1]:
		parts = parts[:-1]

	if self.BASE_PATH:
		parts.insert(0, self.BASE_PATH)

	if self.sandbox_mode:
		parts.insert(0, "test")

	return urljoin(BASE_URL, "/".join(part.strip("/") for part in parts))

def custom_handle_http_code(self, status_code, response_json):
	# GSP connectivity issues
        if status_code == 401 or (
            status_code == 403
            and response_json
            and response_json.get("error") == "access_denied"
        ):
            frappe.throw(
                _(
                    "Error establishing connection to GSP. Please contact India"
                    " Compliance API support at <strong>api-support@finbyz.tech</strong>."
                ),
                title=_("GSP Connection Error"),
            )

        # ASP connectivity issues
        if status_code == 429:
            frappe.throw(
                _("Your India Compliance API credits have exhausted"),
                title=_("API Credits Exhausted"),
            )

        if status_code == 403:
            frappe.throw(
                _("Your India Compliance API key is invalid"),
                title=_("Invalid API Key"),
            )

        if status_code == 504:
            raise GatewayTimeoutError