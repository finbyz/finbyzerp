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

	is_mr_required = (
		buying_settings.is_material_request_required_for_purchase_order == "Yes"
		or company_settings.material_request_mandatory
	)
	if not is_mr_required:
		return

	user_roles = frappe.get_roles(frappe.session.user)

	# Override role bypasses MR requirement entirely, for any item
	allowed_role = buying_settings.role_allowed_to_override_material_request
	if allowed_role and allowed_role in user_roles:
		return

	# If toggle is "Yes", ANY user can skip MR for service items.
	# If "No", only the override role above (already handled) can skip it.
	service_exemption_active = (
		buying_settings.bypass_material_request_required_for_service_item == "Yes"
	)

	missing_material_request_items = []
	for index, item in enumerate(self.items, start=1):
		if item.material_request:
			continue
		if not self.is_new():
			continue
		if service_exemption_active and is_service_item(item.item_code):
			continue
		missing_material_request_items.append(f"{index}. {item.item_code}")

	if missing_material_request_items:
		items_list = "\n".join(missing_material_request_items)
		frappe.throw(f'Material Request is mandatory for the following items:\n{items_list}')


def is_service_item(item_code):
	item_details = frappe.get_cached_value(
		'Item',
		item_code,
		['item_group', 'is_stock_item'],
		as_dict=True
	)
	if not item_details:
		return False
	return (
		item_details.item_group == "Services"
		and item_details.is_stock_item == 0  
	)