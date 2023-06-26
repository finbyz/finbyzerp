import frappe
from frappe import _

def before_rename(self, method, old, new, merge=False):
	fiscal_year_frozen_till_date = frappe.db.get_value("Accounts Settings", None, "fiscal_year_frozen_till_date")
	if fiscal_year_frozen_till_date and merge:
		frappe.throw(
			_("No one Authorized to Merge Customer as Fiscal Year Frozen Date has Applied")
			)
