import frappe
from frappe.utils import flt, cstr

def set_status(self, update=False):
	status = {
		"0": "Draft",
		"1": "Submitted",
		"2": "Cancelled"
	}[cstr(self.docstatus or 0)]

	paid_amount = flt(self.total_amount_reimbursed) + flt(self.total_advance_amount)
	precision = self.precision("grand_total")
	# finbyz change
	if (self.is_paid or (flt(self.total_sanctioned_amount) > 0
			and flt(flt(self.total_sanctioned_amount) + flt(self.total_taxes_and_charges), precision) ==  flt(paid_amount, precision))) \
			and self.docstatus == 1 and self.approval_status == 'Approved':
		status = "Paid"
	elif flt(self.total_sanctioned_amount) > 0 and self.docstatus == 1 and self.approval_status == 'Approved':
		status = "Unpaid"
	elif self.docstatus == 1 and self.approval_status == 'Rejected':
		status = 'Rejected'

	if update:
		self.db_set("status", status)
	else:
		self.status = status
