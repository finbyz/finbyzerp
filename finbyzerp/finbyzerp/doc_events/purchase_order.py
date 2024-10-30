import frappe
from frappe.utils import now

def validate(self, frm):
    other_contact_list(self, frm)
    material_request_required_for_purchase_order(self)

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
        
def material_request_required_for_purchase_order(self):
    buying_settings = frappe.get_single('Buying Settings')
    company_settings = frappe.get_doc('Company', self.company)

    if company_settings.material_request_mandatory:
        allowed_role = buying_settings.role_allowed_to_override_material_request

        if not allowed_role or not frappe.has_permission(doctype='Role', user=frappe.session.user, ptype='read', doc=allowed_role):
            missing_material_request_items = []

            for index, item in enumerate(self.items, start=1):
                if not item.material_request:
                    missing_material_request_items.append(f"{index}. {item.item_code}")

            if missing_material_request_items:
                items_list = "\n".join(missing_material_request_items)
                frappe.throw(f'Material Request is mandatory for the following items:\n{items_list}')
