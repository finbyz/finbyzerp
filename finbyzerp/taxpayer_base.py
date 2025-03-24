import frappe
from finbyzerp.e_invoice_override_14 import get_auth_token
from finbyzerp.get_public_ip import get_public_ip
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
            "ip-usr": frappe.cache().hget("public_ip", "public_ip", get_public_ip),
            "txn": self.generate_request_id(length=32),
        }
    )
