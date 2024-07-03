import frappe
import json
from frappe import _
from frappe.utils import flt

import frappe.utils
from india_compliance.gst_india.constants.__init__ import GST_TAX_TYPES
from frappe.utils import formatdate
# from india_compliance.gst_india.report.gstr_1.gstr_1 import get_invoice_type_for_excel
from india_compliance.gst_india.utils import (
is_overseas_transaction,
)
from india_compliance.gst_india.report.gstr_1.gstr_1 import Gstr1Report as _Gstr1Report
def execute(filters=None):
    return CustomGstr1Report(filters).run()

class CustomGstr1Report(_Gstr1Report):
    def get_row_data_for_invoice(self, invoice_details, tax_rate, item_detail):
        """
        Build row for GSTR-1

        Value mapping from books to GSTR-1 Excel.
        """
        row = {}
        # For CDNR values should be positive
        item_detail.update(
            {
                "taxable_value": abs(flt(item_detail.get("taxable_value", 0), 2)),
                "cess_amount": abs(flt(item_detail.get("cess_amount", 0), 2)),
            }
        )

        for fieldname in self.invoice_fields:
            if (
                self.filters.get("type_of_business") in ("CDNR-REG", "CDNR-UNREG")
                and fieldname == "invoice_value"
            ):

                row[fieldname] = flt(abs(invoice_details.base_rounded_total), 2) or flt(
                    abs(invoice_details.base_grand_total), 2
                )
            elif (
                self.filters.get("type_of_business")
                in ("CDNR-REG", "CDNR-UNREG", "B2B")
                and fieldname == "invoice_type"
            ):
                row[fieldname] = get_invoice_type_for_excel(invoice_details)
            # FINBYZ CHANGES START
            elif fieldname == "invoice_value":
                total_value = invoice_details.base_rounded_total if invoice_details.base_rounded_total > 0 else invoice_details.base_grand_total
                row[fieldname] = flt(total_value - flt(self.export_reverse_charge.get(invoice_details.invoice_number)), 2) or flt(
                    invoice_details.base_grand_total  - flt(self.export_reverse_charge.get(invoice_details.invoice_number)) , 2
                )
            # FINBYZ CHANGES END
            elif fieldname in ("posting_date", "shipping_bill_date"):
                row[fieldname] = formatdate(invoice_details.get(fieldname), "dd-MMM-YY")

            elif fieldname == "export_type":
                export_type = "WPAY" if invoice_details.get(fieldname) else "WOPAY"
                row[fieldname] = export_type
            else:
                row[fieldname] = invoice_details.get(fieldname)

        row.update({"rate": tax_rate, "applicable_tax_rate": 0, **item_detail})

        return row

    def get_invoice_wise_tax_details(self):
        """
        Returns item wise tax details for each invoice.

        Important: Only Updates Tax amounts and Tax Rates.
        Taxable value is updated in get_invoice_tax_rate_info

        Example:
            {
                "INV-001": {
                    "item_code": {
                        "tax_rate": 5,
                        "cess_amount": 0,
                        "taxable_value": 0
                    }
                }
            }
        """
        unidentified_gst_accounts = set()
        invoice_tax_details = frappe.db.sql(
            """
            select
                parent, account_head, item_wise_tax_detail,gst_tax_type
            from `tab%s`
            where
                parenttype = %s and docstatus = 1
                and parent in (%s)
            order by account_head
        """
            % (self.tax_doctype, "%s", ", ".join(["%s"] * len(self.invoices.keys()))),
            tuple([self.doctype] + list(self.invoices.keys())),
        )

        # FINBYZ CHANGES START
        self.export_reverse_charge = {} 
        self.export_reverse_charge_account = frappe.db.sql("""
        select export_reverse_charge_account
        from `tabGST Account`
        where company = %s and account_type = 'Output'
        """, (self.filters.get("company"),), as_dict=1)
        # frappe.throw(str(self.export_reverse_charge_account[0]["export_reverse_charge_account"]))
        # FINBYZ CHANGES END

        invoice_item_wise_tax_details = frappe._dict()

        for parent, account, item_wise_tax_detail, gst_tax_type in invoice_tax_details:
            # FINBYZ CHANGES START
            if account ==  self.export_reverse_charge_account[0]["export_reverse_charge_account"]:
                self.export_reverse_charge[parent] = list(json.loads(item_wise_tax_detail).values())[-1][-1]
            # FINBYZ CHANGES END
            if not item_wise_tax_detail:
                continue

            if gst_tax_type not in GST_TAX_TYPES:
                if "gst" in account.lower():
                    unidentified_gst_accounts.add(account)
                continue
            try:
                item_wise_tax_detail = json.loads(item_wise_tax_detail)
            except ValueError:
                continue

            is_cess = "cess" in gst_tax_type
            is_cgst_or_sgst = gst_tax_type in ("cgst", "sgst")

            parent_dict = invoice_item_wise_tax_details.setdefault(parent, {})
            for item_code, invoice_tax_details in item_wise_tax_detail.items():
                tax_rate = flt(invoice_tax_details[0])
                tax_rate = flt(tax_rate * 2 if is_cgst_or_sgst else tax_rate)
                tax_amount = flt(invoice_tax_details[1])

                item_dict = parent_dict.setdefault(
                    item_code, {"tax_rate": 0, "cess_amount": 0, "taxable_value": 0}
                )

                if is_cess:
                    item_dict["cess_amount"] += tax_amount
                    continue

                item_dict["tax_rate"] = tax_rate

        if unidentified_gst_accounts:
            frappe.msgprint(
                _("Following accounts might be selected in GST Settings:")
                + "<br>"
                + "<br>".join(unidentified_gst_accounts),
                alert=True,
            )

        return invoice_item_wise_tax_details
