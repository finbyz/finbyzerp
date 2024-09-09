import frappe
from india_compliance.gst_india.api_classes.base import get_public_ip
from finbyzerp.finbyzerp.override.india_compliance.e_invoice import get_auth_token
from frappe import _


def setup(self, company_gstin):
    if self.sandbox_mode:
        frappe.throw(_("Sandbox mode not supported for Returns API"))

    self.company_gstin = company_gstin
    self.fetch_credentials(self.company_gstin, "Returns", require_password=False)
    self.default_headers.update(
        {
            "authorization":  get_auth_token(self),
            "gstin": self.company_gstin,
            "state-cd": self.company_gstin[:2],
            "username": self.username,
            "ip-usr": frappe.cache.hget("public_ip", "public_ip", get_public_ip),
            "txn": self.generate_request_id(length=32),
        }
    )