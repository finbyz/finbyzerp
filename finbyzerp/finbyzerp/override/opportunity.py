import frappe

from erpnext.crm.doctype.opportunity.opportunity import Opportunity
class CustomOpportunity(Opportunity):
	def disable_lead(self):
		if self.opportunity_from == "Lead":
			frappe.db.set_value("Lead", self.party_name, {"docstatus": 1})