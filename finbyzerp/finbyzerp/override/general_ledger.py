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

from erpnext.accounts.report.general_ledger.general_ledger import get_result,update_translations,validate_filters ,validate_party,set_account_currency,get_columns

def execute(filters=None):
	if not filters:
		return [], []

	account_details = {}

	if filters and filters.get("print_in_account_currency") and not filters.get("account"):
		frappe.throw(_("Select an account to print in account currency"))

	for acc in frappe.db.sql("""select name, is_group from tabAccount""", as_dict=1):
		account_details.setdefault(acc.name, acc)

	if filters.get("party"):
		filters.party = frappe.parse_json(filters.get("party"))

	validate_filters(filters, account_details)

	validate_party(filters)

	filters = set_account_currency(filters)

	columns = get_columns(filters)

	update_translations()

	res = get_result(filters, account_details)

	if filters.get("account"):
		for row in res:
			if row.get('voucher_no'):
				row.update({'bill_no':frappe.db.get_value(row.voucher_type , row.voucher_no , 'bill_no')})
				frappe.msgprint(str(row.get('bill_no')))

	return columns, res