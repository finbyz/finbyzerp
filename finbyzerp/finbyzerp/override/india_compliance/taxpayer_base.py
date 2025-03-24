import frappe
import requests
from frappe import _
from finbyzerp.finbyzerp.get_public_ip import get_public_ip
from finbyzerp.finbyzerp.override.india_compliance.e_invoice import get_auth_token


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


def get_gstn_public_certificate(self, error_message=None) -> str:
    response = frappe._dict(requests.get("https://asp.resilient.tech/static/gstn_g2b_prod_public").json())

    if response.certificate == self.settings.gstn_public_certificate:
        frappe.throw(error_message or _("Public Certificate is already up to date"))

    self.settings.db_set("gstn_public_certificate", response.certificate)

    return response.certificate
