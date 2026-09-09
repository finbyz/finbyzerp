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

	# Master switch: if not 'Yes', MR validation logic must NOT execute.
	if buying_settings.get('is_material_request_required_for_purchase_order') != 'Yes':
		return

	user_roles = frappe.get_roles(frappe.session.user)
	allowed_role = buying_settings.get('role_allowed_to_override_material_request')

	# 1. If user has the allowed override role, bypass MR requirement for ALL items (stock & service)
	if allowed_role and allowed_role in user_roles:
		return

	# 2. If user does NOT have override role, check if service items can be bypassed
	bypass_service_item = (
		buying_settings.get('bypass_material_request_required_for_service_item') == 'Yes'
	)

	missing_material_request_items = []
	for index, item in enumerate(self.items, start=1):
		if item.material_request:
			continue
		if bypass_service_item and is_service_item(item.item_code):
			continue
		missing_material_request_items.append(f"{index}. {item.item_code}")

	if missing_material_request_items:
		items_list = "\n".join(missing_material_request_items)
		frappe.throw(f'Material Request is mandatory for the following items:\n{items_list}')


def is_service_item(item_code):
	if not item_code:
		return False
	item_details = frappe.get_cached_value(
		'Item',
		item_code,
		['item_group', 'is_stock_item'],
		as_dict=True
	)
	if not item_details:
		return False
	return (
		item_details.get('item_group') == "Services"
		and item_details.get('is_stock_item') == 0  
	)