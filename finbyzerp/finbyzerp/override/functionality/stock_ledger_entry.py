import frappe
from frappe import _
from datetime import date
from frappe.utils import add_days, cint, formatdate, get_datetime, getdate

class StockFreezeError(frappe.ValidationError):
	pass

def check_stock_frozen_date(self):
	stock_settings = frappe.get_cached_doc("Stock Settings")

	if stock_settings.stock_frozen_upto:
		if (
			getdate(self.posting_date) <= getdate(stock_settings.stock_frozen_upto)
			and stock_settings.stock_auth_role not in frappe.get_roles()
		):
			frappe.throw(
				_("Stock transactions before {0} are frozen").format(
					formatdate(stock_settings.stock_frozen_upto)
				),
				StockFreezeError,
			)

	stock_frozen_upto_days = cint(stock_settings.stock_frozen_upto_days)
	if stock_frozen_upto_days:
		older_than_x_days_ago = (
			add_days(getdate(self.posting_date), stock_frozen_upto_days) <= date.today()
		)
		if older_than_x_days_ago and stock_settings.stock_auth_role not in frappe.get_roles():
			frappe.throw(
				_("Not allowed to update stock transactions older than {0}").format(stock_frozen_upto_days),
				StockFreezeError,
			)
	
	fiscal_year_frozen_till_date = frappe.db.get_value("Accounts Settings", None, "fiscal_year_frozen_till_date")
	fiscal_year_frozen_allow_for_admin = frappe.db.get_value("Accounts Settings", None, "fiscal_year_frozen_allow_for_admin")
	
	# Check Above Fields in Accounts Settings and Check Permission Level as Well
	if cint(fiscal_year_frozen_allow_for_admin) and frappe.session.user == "Administrator":
		return

	if fiscal_year_frozen_till_date and getdate(self.posting_date) <= getdate(fiscal_year_frozen_till_date):
		frappe.throw(
			_("No one authorized to add or update entries before {0}").format(
				formatdate(fiscal_year_frozen_till_date)
			)
		)