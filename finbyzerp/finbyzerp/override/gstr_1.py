import frappe
import json
from frappe import _
from frappe.utils import cint, flt, formatdate, getdate
from india_compliance.gst_india.report.gstr_1.gstr_1 import get_invoice_type_for_excel
from india_compliance.gst_india.utils import (
    is_overseas_transaction,
)
def get_row_data_for_invoice(self, invoice, invoice_details, tax_rate, items):
        row = {}
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
        taxable_value = 0
        cess_amount = 0

        for item_code, net_amount in self.invoice_items.get(invoice).items():
            if item_code in items:
                taxable_value += flt(abs(net_amount), 2)
                cess_amount += flt(
                    self.invoice_cess.get(invoice, {}).get(item_code, 0.0), 2
                )

        row["rate"] = tax_rate or 0
        row["taxable_value"] = taxable_value
        row["applicable_tax_rate"] = 0

        for column in self.other_columns:
            if column.get("fieldname") == "cess_amount":
                row["cess_amount"] = cess_amount

        return row, taxable_value


def get_items_based_on_tax_rate(self):
        tax_details = frappe.db.sql(
            """
			select
				parent, account_head, item_wise_tax_detail
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
        self.items_based_on_tax_rate = {}
        self.invoice_cess = frappe._dict()

        unidentified_gst_accounts = set()
        unidentified_gst_accounts_invoice = set()
        for parent, account, item_wise_tax_detail in tax_details:
            # FINBYZ CHANGES START
            if account ==  self.export_reverse_charge_account[0]["export_reverse_charge_account"]:
                self.export_reverse_charge[parent] = list(json.loads(item_wise_tax_detail).values())[-1][-1]
            # FINBYZ CHANGES END
            if not item_wise_tax_detail:
                continue
            if account not in self.gst_accounts.values():
                if "gst" in account.lower():
                    unidentified_gst_accounts.add(account)
                    unidentified_gst_accounts_invoice.add(parent)

                continue

            try:
                item_wise_tax_detail = json.loads(item_wise_tax_detail)
            except ValueError:
                continue

            is_cess = account == self.gst_accounts.cess_account
            is_cgst_or_sgst = (
                account == self.gst_accounts.cgst_account
                or account == self.gst_accounts.sgst_account
            )

            for item_code, tax_amounts in item_wise_tax_detail.items():
                tax_rate = tax_amounts[0]

                if not tax_rate and parent not in self.nil_exempt_non_gst:
                    continue

                if is_cess:
                    self.invoice_cess.setdefault(parent, {})
                    self.invoice_cess[parent].setdefault(item_code, 0.0)
                    self.invoice_cess[parent][item_code] += tax_amounts[1]
                    continue

                if is_cgst_or_sgst:
                    tax_rate *= 2

                (
                    self.items_based_on_tax_rate.setdefault(parent, {})
                    .setdefault(tax_rate, set())
                    .add(item_code)
                )

        if unidentified_gst_accounts:
            frappe.msgprint(
                _("Following accounts might be selected in GST Settings:")
                + "<br>"
                + "<br>".join(unidentified_gst_accounts),
                alert=True,
            )

        # Build itemised tax for export invoices where tax table is blank
        for invoice_no, items in self.invoice_items.items():
            if (
                invoice_no in self.items_based_on_tax_rate
                or invoice_no in unidentified_gst_accounts_invoice
            ):
                continue

            invoice = self.invoices.get(invoice_no, {})
            if not invoice.get("is_export_with_gst") and is_overseas_transaction(
                "Sales Invoice", invoice.gst_category, invoice.place_of_supply
            ):
                self.items_based_on_tax_rate.setdefault(invoice_no, {}).setdefault(
                    0, []
                ).extend(items)

            # Show invoice with all items are in nil exempt and exclude non-gst
            if (
                invoice_no in self.nil_exempt_non_gst
                and self.nil_exempt_non_gst[invoice_no][2] == 0
            ):
                self.items_based_on_tax_rate.setdefault(invoice_no, {}).setdefault(
                    0, []
                ).extend(items)