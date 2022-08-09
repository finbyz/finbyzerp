from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, cstr, flt, date_diff
from erpnext.accounts.utils import get_fiscal_year
from erpnext.accounts.utils import unlink_ref_doc_from_payment_entries