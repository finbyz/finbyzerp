import frappe
from frappe.utils import now


def before_cancel(self, method):
    frappe.db.sql(
        """update `tabGL Entry`
		set against_voucher_type=null, against_voucher=null,
		modified=%s, modified_by=%s
		where against_voucher_type=%s and against_voucher=%s
		and voucher_no != ifnull(against_voucher, '') and is_cancelled = 1""",
        (now(), frappe.session.user, self.doctype, self.name),
    )

def validate(self, frm):
    other_contact_list(self, frm)

def other_contact_list(self, frm):
    email_lst = [self.contact_email] if self.contact_email else []
    email_lst += [row.email_id for row in self.other_contacts if row.email_id]
    
    if email_lst:
        self.email = ", ".join(email_lst)
