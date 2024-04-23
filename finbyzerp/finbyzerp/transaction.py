import frappe
import json

import frappe
from frappe import _, bold
from frappe.model import delete_doc
from frappe.utils import cint, flt
from erpnext.controllers.accounts_controller import get_taxes_and_charges
from erpnext.controllers.taxes_and_totals import (
    get_itemised_tax,
    get_itemised_taxable_amount,
)
from india_compliance.gst_india.overrides.transaction import (get_valid_accounts, is_export_without_payment_of_gst, is_inter_state_supply)
from india_compliance.gst_india.constants import (
    GST_TAX_TYPES,
    SALES_DOCTYPES,
    STATE_NUMBERS,
)
from india_compliance.gst_india.constants.custom_fields import E_WAYBILL_INV_FIELDS
from india_compliance.gst_india.doctype.gstin.gstin import (
    _validate_gstin_info,
    get_gstin_status,
)
from india_compliance.gst_india.utils import (
    get_all_gst_accounts,
    get_gst_accounts_by_tax_type,
    get_gst_accounts_by_type,
    get_hsn_settings,
    get_place_of_supply,
    get_place_of_supply_options,
    is_overseas_doc,
    join_list_with_custom_separators,
    validate_gst_category,
)
from india_compliance.income_tax_india.overrides.tax_withholding_category import (
    get_tax_withholding_accounts,
)

DOCTYPES_WITH_GST_DETAIL = {
    "Supplier Quotation",
    "Purchase Order",
    "Purchase Receipt",
    "Purchase Invoice",
    "Quotation",
    "Sales Order",
    "Delivery Note",
    "Sales Invoice",
    "POS Invoice",
}


def validate_gst_accounts(doc, is_sales_transaction=False):
    """
    Validate GST accounts
    - Only Valid Accounts should be allowed
    - No GST account should be specified for transactions where Company GSTIN = Party GSTIN
    - If export is made without GST, then no GST account should be specified
    - SEZ / Inter-State supplies should not have CGST or SGST account
    - Intra-State supplies should not have IGST account
    """
    if not doc.taxes:
        return

    if not (
        rows_to_validate := [
            row
            for row in doc.taxes
            if row.tax_amount and row.account_head in get_all_gst_accounts(doc.company)
        ]
    ):
        return

    # Helper functions

    def _get_matched_idx(rows_to_search, account_head_list):
        return next(
            (
                row.idx
                for row in rows_to_search
                if row.account_head in account_head_list
            ),
            None,
        )

    def _throw(message, title=None):
        frappe.throw(message, title=title or _("Invalid GST Account"))

    all_valid_accounts, intra_state_accounts, inter_state_accounts = get_valid_accounts(
        doc.company,
        for_sales=is_sales_transaction,
        for_purchase=not is_sales_transaction,
    )
    cess_non_advol_accounts = get_gst_accounts_by_tax_type(
        doc.company, "cess_non_advol"
    )

    # Company GSTIN = Party GSTIN
    party_gstin = (
        doc.billing_address_gstin if is_sales_transaction else doc.supplier_gstin
    )
    if (
        party_gstin
        and doc.company_gstin == party_gstin
        and (idx := _get_matched_idx(rows_to_validate, all_valid_accounts))
    ):
        _throw(
            _(
                "Cannot charge GST in Row #{0} since Company GSTIN and Party GSTIN are"
                " same"
            ).format(idx)
        )

    # Sales / Purchase Validations
    if is_sales_transaction:
        if is_export_without_payment_of_gst(doc) and (
            idx := _get_matched_idx(rows_to_validate, all_valid_accounts)
        ):
            _throw(
                _(
                    "Cannot charge GST in Row #{0} since export is without"
                    " payment of GST"
                ).format(idx)
            )

        if doc.get("is_reverse_charge") and (
            idx := _get_matched_idx(rows_to_validate, all_valid_accounts)
        ):
            _throw(
                _(
                    "Cannot charge GST in Row #{0} since supply is under reverse charge"
                ).format(idx)
            )

    elif doc.gst_category == "Registered Composition" and (
        idx := _get_matched_idx(rows_to_validate, all_valid_accounts)
    ):
        _throw(
            _(
                "Cannot claim Input GST in Row #{0} since purchase is being made from a"
                " dealer registered under Composition Scheme"
            ).format(idx)
        )

    elif not doc.is_reverse_charge:
        if idx := _get_matched_idx(
            rows_to_validate,
            get_gst_accounts_by_type(doc.company, "Reverse Charge").values(),
        ):
            _throw(
                _(
                    "Cannot use Reverse Charge Account in Row #{0} since purchase is"
                    " without Reverse Charge"
                ).format(idx)
            )

        if not doc.supplier_gstin and (
            idx := _get_matched_idx(rows_to_validate, all_valid_accounts)
        ):
            _throw(
                _(
                    "Cannot charge GST in Row #{0} since purchase is from a Supplier"
                    " without GSTIN"
                ).format(idx)
            )

    is_inter_state = is_inter_state_supply(doc)
    previous_row_references = set()

    for row in rows_to_validate:
        account_head = row.account_head

        if row.charge_type == "Actual":
            item_tax_detail = frappe.parse_json(row.get("item_wise_tax_detail") or {})
            for tax_rate, tax_amount in item_tax_detail.values():
                if tax_amount and not tax_rate:
                    #Finbyz Changes start
                    if is_sales_transaction:
                    #finbyz changes End
                        _throw(
                            _(
                                "Tax Row #{0}: Charge Type is set to Actual. However, this would"
                                " not compute item taxes, and your further reporting will be affected."
                            ).format(row.idx),
                            title=_("Invalid Charge Type"),
                        )

        if account_head not in all_valid_accounts:
            _throw(
                _("{0} is not a valid GST account for this transaction").format(
                    bold(account_head)
                ),
            )

        # Inter State supplies should not have CGST or SGST account
        if is_inter_state:
            if account_head in intra_state_accounts:
                _throw(
                    _(
                        "Row #{0}: Cannot charge CGST/SGST for inter-state supplies"
                    ).format(row.idx),
                )

        # Intra State supplies should not have IGST account
        elif account_head in inter_state_accounts:
            _throw(
                _("Row #{0}: Cannot charge IGST for intra-state supplies").format(
                    row.idx
                ),
            )

        if row.charge_type == "On Previous Row Amount":
            _throw(
                _(
                    "Row #{0}: Charge Type cannot be <strong>On Previous Row"
                    " Amount</strong> for a GST Account"
                ).format(row.idx),
                title=_("Invalid Charge Type"),
            )

        if row.charge_type == "On Previous Row Total":
            previous_row_references.add(row.row_id)

        if (
            row.charge_type == "On Item Quantity"
            and account_head not in cess_non_advol_accounts
        ):
            _throw(
                _(
                    "Row #{0}: Charge Type cannot be <strong>On Item Quantity</strong>"
                    " as it is not a Cess Non Advol Account"
                ).format(row.idx),
                title=_("Invalid Charge Type"),
            )

        if (
            row.charge_type != "On Item Quantity"
            and account_head in cess_non_advol_accounts
        ):
            _throw(
                _(
                    "Row #{0}: Charge Type must be <strong>On Item Quantity</strong>"
                    " as it is a Cess Non Advol Account"
                ).format(row.idx),
                title=_("Invalid Charge Type"),
            )

    used_accounts = set(row.account_head for row in rows_to_validate)
    if not is_inter_state:
        if used_accounts and not set(intra_state_accounts[:2]).issubset(used_accounts):
            _throw(
                _(
                    "Cannot use only one of CGST or SGST account for intra-state"
                    " supplies"
                ),
                title=_("Invalid GST Accounts"),
            )

    if len(previous_row_references) > 1:
        _throw(
            _(
                "Only one row can be selected as a Reference Row for GST Accounts with"
                " Charge Type <strong>On Previous Row Total</strong>"
            ),
            title=_("Invalid Reference Row"),
        )

    for row in doc.get("items") or []:
        if not row.item_tax_template:
            continue

        for account in used_accounts:
            if account in row.item_tax_rate:
                continue

            frappe.msgprint(
                _(
                    "Item Row #{0}: GST Account {1} is missing in Item Tax Template {2}"
                ).format(row.idx, bold(account), bold(row.item_tax_template)),
                title=_("Invalid Item Tax Template"),
                indicator="orange",
            )

    return all_valid_accounts

def set_for_no_taxes(self):
        for item in self.doc.items:
            if item.gst_treatment not in ("Exempted", "Non-GST"):
                item.gst_treatment = "Nil-Rated"
            if self.doc.gst_category == "Overseas":
                item.gst_treatment = "Taxable"