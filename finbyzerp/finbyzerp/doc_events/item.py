import frappe
from frappe import _
from frappe.utils import add_days, cint, formatdate, get_datetime, getdate

def validate(self,method):
	before_validate(self,method)
	if self.is_new() and not self.is_stock_item:
		for row in self.item_defaults:
			if not row.expense_account:
				frappe.msgprint("Please define correct expense account in Item Defaults.<br>In absence of same expense will be parked in 'Cost of Goods Sold' account")
		# frappe.msgprint("Please define correct expense account in Item Defaults.<br>In absence of same expense will be parked in 'Cost of Goods Sold' account")

def before_validate(self,method):
	if "'" in self.item_code or '"' in self.item_code:
		frappe.throw(""" Item Code not allowed with any special Characters like " or ' """)

def before_rename(self, method, old, new, merge=False):
	fiscal_year_frozen_till_date = frappe.db.get_value("Accounts Settings", None, "fiscal_year_frozen_till_date")
	if fiscal_year_frozen_till_date and merge:
		frappe.throw(
			_("No one Authorized to Merge Items as Fiscal Year Frozen Date has Applied")
			)