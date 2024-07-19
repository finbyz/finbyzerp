import frappe
import requests
from frappe import _


def get_gstn_public_certificate(self, error_message=None) -> str:
    response = frappe._dict(requests.get("https://asp.resilient.tech/static/gstn_g2b_prod_public").json())

    if response.certificate == self.settings.gstn_public_certificate:
        frappe.throw(error_message or _("Public Certificate is already up to date"))

    self.settings.db_set("gstn_public_certificate", response.certificate)

    return response.certificate