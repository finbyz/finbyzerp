from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, cstr, flt, date_diff
from erpnext.accounts.utils import get_fiscal_year



def validate(self, method):
    tcs_deduction(self)
    calculate_gst_taxable_value(self)

def calculate_gst_taxable_value(self):
	self.gst_taxable_value = abs(sum([flt(i.get('taxable_value')) for i in self.get('items')]))

def tcs_deduction(self):
    fiscal_year, fiscal_start_date, fiscal_end_date = get_fiscal(self.posting_date)
    payment_query = frappe.db.sql("""
        select sum(paid_amount)
        from `tabPayment Entry`
        where docstatus = 1 and party = '{}' and company ='{}' and posting_date between '{}' AND '{}'
        group by party
        order by posting_date
    """.format(self.customer,self.company,fiscal_start_date,fiscal_end_date))

    invoice_query = frappe.db.sql("""
        select sum(grand_total)
        from `tabSales Invoice`
        where docstatus = 1 and customer = '{}' and company ='{}' and posting_date between '{}' AND '{}'
        group by customer
        order by posting_date
    """.format(self.customer,self.company,fiscal_start_date,fiscal_end_date))

    if payment_query:
        payment_amount = payment_query[0][0]
    else:
        payment_amount = 0

    if invoice_query:
        invoice_amount = invoice_query[0][0]
    else:
        invoice_amount = 0

    tcs_account = frappe.db.get_value("GST Account",{"parent":"GST Settings","company":"{}".format(self.company)},'tcs_account')
    account_head_list = [tax.account_head for tax in self.taxes]
 
    if payment_amount > 5000000:
        if tcs_account not in account_head_list:          
            frappe.msgprint("Total amount received from <b>{}</b> in fiscal year - <b>{}</b> is <b>{}</b>, As per rules TCS should be applicable".format(self.customer,fiscal_year,payment_amount))
            return
        for tax in self.taxes:
            if tax.account_head == tcs_account and not tax.tax_amount > 0:
                frappe.msgprint("Total amount received from <b>{}</b> in fiscal year - <b>{}</b> is <b>{}</b>, As per rules TCS should be applicable".format(self.customer,fiscal_year,payment_amount))
                return

    if invoice_amount > 5000000:        
        if tcs_account not in account_head_list:          
            frappe.msgprint("Total amount invoiced from <b>{}</b> in fiscal year - <b>{}</b> is <b>{}</b>, As per rules TCS should be applicable".format(self.customer,fiscal_year,invoice_amount))
            return
        for tax in self.taxes:
            if tax.account_head == tcs_account and not tax.tax_amount > 0:
                frappe.msgprint("Total amount invoiced from <b>{}</b> in fiscal year - <b>{}</b> is <b>{}</b>, As per rules TCS should be applicable".format(self.customer,fiscal_year,invoice_amount))
                return

def get_fiscal(date):
    from erpnext.accounts.utils import get_fiscal_year
    fiscal_year = get_fiscal_year(date)
    return str(fiscal_year[0]),str(fiscal_year[1]),str(fiscal_year[2])
