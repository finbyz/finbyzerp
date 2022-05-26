import frappe, erpnext
from frappe import _
from frappe.utils import cint, cstr, flt, formatdate, getdate, now

def check_freezing_date(posting_date, adv_adj=False):
	"""
	Nobody can do GL Entries where posting date is before freezing date
	except authorized person

	Administrator has all the roles so this check will be bypassed if any role is allowed to post
	Hence stop admin to bypass if accounts are freezed
	"""
	if not adv_adj:
		acc_frozen_upto = frappe.db.get_value("Accounts Settings", None, "acc_frozen_upto")
		if acc_frozen_upto:
			frozen_accounts_modifier = frappe.db.get_value(
				"Accounts Settings", None, "frozen_accounts_modifier"
			)
			if getdate(posting_date) <= getdate(acc_frozen_upto) and (
				frozen_accounts_modifier not in frappe.get_roles() or frappe.session.user == "Administrator"
			):
				frappe.throw(
					_("You are not authorized to add or update entries before {0}").format(
						formatdate(acc_frozen_upto)
					)
				)
	
	fiscal_year_frozen_till_date = frappe.db.get_value("Accounts Settings", None, "fiscal_year_frozen_till_date")
	fiscal_year_frozen_allow_for_admin = frappe.db.get_value("Accounts Settings", None, "fiscal_year_frozen_allow_for_admin")
	
	# Check Above Fields in Accounts Settings and Check Permission Level as Well
	if cint(fiscal_year_frozen_allow_for_admin) and frappe.session.user == "Administrator":
		return
	
	if fiscal_year_frozen_till_date and getdate(posting_date) <= getdate(fiscal_year_frozen_till_date):
		frappe.throw(
			_("No one authorized to add or update entries before {0}").format(
				formatdate(fiscal_year_frozen_till_date)
			)
		)