import frappe
from frappe.contacts.doctype.address.address import get_company_address
from erpnext.accounts.party import get_party_account
from frappe.model.utils import get_fetch_values
from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from frappe.model.mapper import get_mapped_doc
from erpnext.accounts.utils import get_fiscal_year, flt
@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None, ignore_permissions=False):
    def postprocess(source, target):
        set_missing_values(source, target)
        # Get the advance paid Journal Entries in Sales Invoice Advance
        if target.get("allocate_advances_automatically"):
            target.set_advances()

    def set_missing_values(source, target):
        target.flags.ignore_permissions = True
        target.run_method("set_missing_values")
        target.run_method("set_po_nos")
        target.run_method("calculate_taxes_and_totals")

        if source.company_address:
            target.update({"company_address": source.company_address})
        else:
            # set company address
            target.update(get_company_address(target.company))

        if target.company_address:
            target.update(get_fetch_values("Sales Invoice", "company_address", target.company_address))

        # set the redeem loyalty points if provided via shopping cart
        if source.loyalty_points and source.order_type == "Shopping Cart":
            target.redeem_loyalty_points = 1

        target.debit_to = get_party_account("Customer", source.customer, source.company)

    def update_item(source, target, source_parent):
        target.amount = flt(source.amount) - flt(source.billed_amt)
        target.base_amount = target.amount * flt(source_parent.conversion_rate)
        target.qty = (
            target.amount / flt(source.rate)
            if (source.rate and source.billed_amt)
            else source.qty - source.returned_qty
        )

        if source_parent.project:
            target.cost_center = frappe.db.get_value("Project", source_parent.project, "cost_center")
        if target.item_code:
            item = get_item_defaults(target.item_code, source_parent.company)
            item_group = get_item_group_defaults(target.item_code, source_parent.company)
            cost_center = item.get("selling_cost_center") or item_group.get("selling_cost_center")

            if cost_center:
                target.cost_center = cost_center

    doclist = get_mapped_doc(
        "Sales Order",
        source_name,
        {
            "Sales Order": {
                "doctype": "Sales Invoice",
                "field_map": {
                    "party_account_currency": "party_account_currency",
                    "payment_terms_template": "payment_terms_template",
                    "payment_terms_template":"payment_terms_template"
                },
                "validation": {"docstatus": ["=", 1]},
            },
            "Sales Order Item": {
                "doctype": "Sales Invoice Item",
                "field_map": {
                    "name": "so_detail",
                    "parent": "sales_order",
                },
                "postprocess": update_item,
                "condition": lambda doc: doc.qty
                and (doc.base_amount == 0 or abs(doc.billed_amt) < abs(doc.amount)),
            },
            "Payment Schedule":{
            "doctype":"Payment Schedule",
            "field_map":{
                "name":"payment_schedule",
                "payment_term":"payment_term",
                "due_date":"due_date",
                "invoice_portion":"invoice_portion",
                "discount_type":"discount_type",
                "discount":"discount",
                "payment_amount":"payment_amount",
                "base_payment_amount":"base_payment_amount",
                "outstanding":"outstanding"
            }
        },
            "Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
            "Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
        },
        target_doc,
        postprocess,
        ignore_permissions=ignore_permissions,
    )

    automatically_fetch_payment_terms = cint(
        frappe.db.get_single_value("Accounts Settings", "automatically_fetch_payment_terms")
    )
    if automatically_fetch_payment_terms:
        doclist.set_payment_schedule()

    return doclist
