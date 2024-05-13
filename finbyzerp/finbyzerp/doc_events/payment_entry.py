from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from erpnext.accounts.general_ledger import make_reverse_gl_entries
from erpnext.accounts.utils import create_payment_ledger_entry

# def validate(self,method):
# 	update_jv_exchange_rate(self)

# def update_jv_exchange_rate(self):
# 	set_exchange_rate = False
# 	if self.get('references'):
# 		for ref in self.get('references'):
# 			if ref.reference_doctype == "Journal Entry":
# 				exchange_rate = frappe.db.get_value("Journal Entry Account",{"parent":ref.reference_name,"party_type":self.party_type,"party":self.party},"exchange_rate")
# 				if exchange_rate and ref.exchange_rate != exchange_rate:
# 					ref.exchange_rate = exchange_rate
# 					set_exchange_rate = True
	
# 	if set_exchange_rate:
# 		self.set_tax_withholding()
# 		self.apply_taxes()
# 		self.set_amounts()
# 		self.clear_unallocated_reference_document_rows()
# 		self.validate_payment_against_negative_invoice()
# 		self.set_remarks()
# 		self.validate_allocated_amount()
# 		self.set_status()



@frappe.whitelist()
def unallocate_payment(child_doc_name,parent_doc_name,reference_doctype,reference_name,adv_adj=False, update_outstanding="Yes"):
	if reference_doctype in ['Sales Invoice','Purchase Invoice']:
		doc = frappe.get_doc("Payment Entry",parent_doc_name)
		gl_map = doc.build_gl_map()
		create_payment_ledger_entry(gl_map, cancel = 1, adv_adj = adv_adj)
		frappe.db.sql(f"delete from `tabPayment Entry Reference` where name = '{child_doc_name}'")
		doc = frappe.get_doc("Payment Entry",parent_doc_name)
		doc.set_amounts()
		doc.db_update()
		gl_map = doc.build_gl_map()
		create_payment_ledger_entry(gl_map, cancel = 0, adv_adj = adv_adj)

		# doc.make_gl_entries(cancel=1)
		# doc.make_gl_entries(cancel=0)	
		
		# make_reverse_gl_entries()

		update_outstanding_amt(
			doc.paid_from if doc.payment_type == "Receive" else doc.paid_to,
			doc.party_type,
			doc.party,
			reference_doctype,
			reference_name
		)

		ref_doc = frappe.get_doc(reference_doctype, reference_name)
		ref_doc.delink_advance_entries(doc.name)


		return "Payment Unallocated Successfully"
	else:
		return "Not able to Unallocate the Payment"
	

def update_outstanding_amt(account, party_type, party, against_voucher_type, against_voucher):
	if party_type and party:
		party_condition = " and party_type={0} and party={1}"\
			.format(frappe.db.escape(party_type), frappe.db.escape(party))
	else:
		party_condition = ""

	if against_voucher_type == "Sales Invoice":
		party_account = frappe.db.get_value(against_voucher_type, against_voucher, "debit_to")
		account_condition = "and account in ({0}, {1})".format(frappe.db.escape(account), frappe.db.escape(party_account))
	else:
		account_condition = " and account = {0}".format(frappe.db.escape(account))

	# get final outstanding amt
	bal = flt(frappe.db.sql("""
		select sum(debit_in_account_currency) - sum(credit_in_account_currency)
		from `tabGL Entry`
		where is_cancelled = 0 and against_voucher_type=%s and against_voucher=%s
		and voucher_type != 'Invoice Discounting'
		{0} {1}""".format(party_condition, account_condition),
		(against_voucher_type, against_voucher))[0][0] or 0.0)

	if against_voucher_type == 'Purchase Invoice':
		bal = -bal

	if against_voucher_type in ["Sales Invoice", "Purchase Invoice"]:
		ref_doc = frappe.get_doc(against_voucher_type, against_voucher)

		# Didn't use db_set for optimisation purpose
		ref_doc.outstanding_amount = bal
		frappe.db.set_value(against_voucher_type, against_voucher, 'outstanding_amount', bal)

		ref_doc.set_status(update=True)


def validate(self, frm):
    other_contact_list(self, frm)

def on_update_after_submit(self,frm):
    other_contact_list(self, frm)

def other_contact_list(self, frm):
    email_lst = [self.contact_email] if self.contact_email else []
    email_lst += [row.email_id for row in self.other_contacts if row.email_id]
    
    if email_lst:
        self.email = ", ".join(email_lst)
        self.db_set("email", self.email)
        
    else:
        self.email = " "
        self.db_set("email", self.email)