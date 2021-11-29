from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, cstr, flt, date_diff
from erpnext.accounts.utils import get_fiscal_year
from erpnext.accounts.utils import unlink_ref_doc_from_payment_entries

def before_submit(self, method):
    unlink_debit_note_entries(self)

def unlink_debit_note_entries(self):
    if self.is_return and self.return_against:
        unlink_ref_doc_from_payment_entries(frappe.get_doc("Purchase Invoice",self.return_against))