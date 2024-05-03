import frappe
from erpnext.setup.doctype.authorization_rule.authorization_rule import AuthorizationRule as _AuthorizationRule


class AuthorizationRule(_AuthorizationRule):
	def validate_rule(self):
		if not self.approving_role and not self.approving_user:
			frappe.throw(_("Please enter Approving Role or Approving User"))
		elif self.system_user and self.system_user == self.approving_user:
			frappe.throw(_("Approving User cannot be same as user the rule is Applicable To"))
		elif self.system_role and self.system_role == self.approving_role:
			frappe.throw(_("Approving Role cannot be same as role the rule is Applicable To"))
		elif self.transaction in [
			"Purchase Order",
			"Purchase Receipt",
			"Purchase Invoice",
			"Stock Entry",
		] and self.based_on in [
			"Average Discount",
			"Customerwise Discount",
			"Itemwise Discount",
		]:
			frappe.throw(
				_("Cannot set authorization on basis of Discount for {0}").format(self.transaction)
			)
		elif self.based_on == "Average Discount" and flt(self.value) > 100.00:
			frappe.throw(_("Discount must be less than 100"))
		elif self.based_on == "Customerwise Discount" and not self.master_name:
			frappe.throw(_("Customer required for 'Customerwise Discount'"))
		# finbyz changes start
		# else:
		# 	self.based_on = "Not Applicable"
		# finbyz changes end