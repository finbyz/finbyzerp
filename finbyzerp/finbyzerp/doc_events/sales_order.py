import frappe
from frappe.utils import now

def validate(self, frm):
    other_contact_list(self, frm)

def on_update_after_submit(self,frm):
    other_contact_list(self, frm)

def other_contact_list(self, frm):
    
    email_lst = [self.contact_email] if self.contact_email else []
    email_lst += [row.email_id for row in self.other_contacts if row.email_id]
    
    if email_lst:
        self.email = ", ".join(email_lst)
        frappe.db.set_value("Purchase Order", self.name, "email", self.email)
        
    else:
        self.email = " "
        frappe.db.set_value("Purchase Order", self.name, "email", " ")