import os
from finbyzerp.finbyzerp.override.india_compliance.e_invoice import get_auth_token
import frappe
import base64

def get_gstin_info(self, gstin):
	self.BASE_PATH = "enriched/commonapi"
	self.gst_settings = frappe.get_cached_doc("GST Settings")
	self.default_headers = {
		"authorization": get_auth_token(self),
		"requestid": self.generate_request_id(),
	}
	response = self.get("search", params={"action": "TP", "gstin": gstin})
	
	if self.sandbox_mode:
		response.update(
			{
				"tradeNam": "Finbyz Tech Pvt. Ltd.",
				"lgnm": "Finbyz Tech Tech Pvt. Ltd.",
			}
		)

	return response
