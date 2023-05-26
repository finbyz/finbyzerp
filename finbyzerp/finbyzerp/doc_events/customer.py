import frappe
from frappe import _

def before_rename(self, method, old, new, merge=False):
	fiscal_year_frozen_till_date = frappe.db.get_value("Accounts Settings", None, "fiscal_year_frozen_till_date")
	if fiscal_year_frozen_till_date and merge:
		frappe.throw(
			_("No one Authorized to Merge Customer as Fiscal Year Frozen Date has Applied")
			)

def make_contact(args, is_primary_contact=1):
	contact = frappe.get_doc(
		{
			"doctype": "Contact",
			"first_name": args.get("first_name"),
			"is_primary_contact": is_primary_contact,
			"links": [{"link_doctype": args.get("doctype"), "link_name": args.get("name")}],
		}
	)
	if args.get("email_id"):
		contact.add_email(args.get("email_id"), is_primary=True)
	if args.get("mobile_no"):
		contact.add_phone(args.get("mobile_no"), is_primary_mobile_no=True)
	contact.insert()

	return contact