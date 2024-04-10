import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.utils import get_fiscal_year


def validate(self, method):
    tcs_deduction(self)
    calculate_gst_taxable_value(self)
    other_contact_list(self)


def before_save(self, method):
    set_shipping_address(self)


def set_shipping_address(self):
    if self.customer_address and not self.shipping_address_name:
        self.shipping_address_name = self.customer_address
        self.customer_gstin = self.billing_address_gstin
        self.shipping_address = self.address_display


def on_trash(self, method):
    validate_irn_generated_invoice(self)

def on_submit(self, method):
	if self.get('eway_bill_json_required'):
		if not self.billing_address_gstin:
			frappe.throw("Billing Address GSTIN is required.")
		
		if not self.customer_gstin:
			frappe.throw("Customer GSTIN is required.")
		
		if not self.distance:
			frappe.throw("Distance (in km) is required.")
		
		if self.distance > 4000:
			frappe.throw("Distance cannot be greater than 4000 kms")
		
		if not self.customer_address:
			frappe.throw("Customer Address is required.")

		if self.customer_address:
			if not frappe.db.get_value("Address", self.customer_address, 'pincode'):
				frappe.throw("Customer Postal Code is required.")
		
		for item in self.items:
			if not item.gst_hsn_code and not item.is_non_gst:
				frappe.throw("Row: {} HSN/SAC is reuired for item {}".format(item.idx, item.item_code))


def validate_irn_generated_invoice(self):
    if (
        self.get("irn")
        or self.get("ewaybill")
        or self.get("irn_cancelled")
        or self.get("eway_bill_cancelled")
    ):
        frappe.throw(
            "Once the E-Invoice (IRN) is cancelled, the same invoice number cannot be re-used to generate another IRN",
            title="IRN or E-way Bill Generated Invoice Cannot be deleted" "",
        )


def calculate_gst_taxable_value(self):
    self.gst_taxable_value = abs(
        sum([flt(i.get("taxable_value")) for i in self.get("items")])
    )


def tcs_deduction(self):
    fiscal_year, fiscal_start_date, fiscal_end_date = get_fiscal(self.posting_date)
    payment_query = frappe.db.sql(
        """
        select sum(paid_amount)
        from `tabPayment Entry`
        where docstatus = 1 and party = "{}" and company ="{}" and posting_date between '{}' AND '{}'
        group by party
        order by posting_date
    """.format(
            self.customer, self.company, fiscal_start_date, fiscal_end_date
        )
    )

    invoice_query = frappe.db.sql(
        """
        select sum(grand_total)
        from `tabSales Invoice`
        where docstatus = 1 and customer = "{}" and company ="{}" and posting_date between '{}' AND '{}'
        group by customer
        order by posting_date
    """.format(
            self.customer, self.company, fiscal_start_date, fiscal_end_date
        )
    )

    if payment_query:
        payment_amount = payment_query[0][0]
    else:
        payment_amount = 0

    if invoice_query:
        invoice_amount = invoice_query[0][0]
    else:
        invoice_amount = 0

    tcs_account = frappe.db.get_value(
        "GST Account",
        {"parent": "GST Settings", "company": "{}".format(self.company)},
        "tcs_account",
    )
    account_head_list = [tax.account_head for tax in self.taxes]

    if payment_amount > 5000000:
        if tcs_account not in account_head_list:
            frappe.msgprint(
                "Total amount received from <b>{}</b> in fiscal year - <b>{}</b> is <b>{}</b>, As per rules TCS should be applicable".format(
                    self.customer, fiscal_year, payment_amount
                )
            )
            return
        for tax in self.taxes:
            if tax.account_head == tcs_account and not tax.tax_amount > 0:
                frappe.msgprint(
                    "Total amount received from <b>{}</b> in fiscal year - <b>{}</b> is <b>{}</b>, As per rules TCS should be applicable".format(
                        self.customer, fiscal_year, payment_amount
                    )
                )
                return

    if invoice_amount > 5000000:
        if tcs_account not in account_head_list:
            frappe.msgprint(
                "Total amount invoiced from <b>{}</b> in fiscal year - <b>{}</b> is <b>{}</b>, As per rules TCS should be applicable".format(
                    self.customer, fiscal_year, invoice_amount
                )
            )
            return
        for tax in self.taxes:
            if tax.account_head == tcs_account and not tax.tax_amount > 0:
                frappe.msgprint(
                    "Total amount invoiced from <b>{}</b> in fiscal year - <b>{}</b> is <b>{}</b>, As per rules TCS should be applicable".format(
                        self.customer, fiscal_year, invoice_amount
                    )
                )
                return


def get_fiscal(date):
    fiscal_year = get_fiscal_year(date)
    return str(fiscal_year[0]), str(fiscal_year[1]), str(fiscal_year[2])


def other_contact_list(self):
    email_lst = []
    email_lst.append(self.contact_email)
    for row in self.other_contacts:
        if row.email_id:
            email_lst.append(row.email_id)
    combined_emails = ", ".join(email_lst)
    self.email = combined_emails