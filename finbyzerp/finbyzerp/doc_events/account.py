from __future__ import unicode_literals
import frappe
#import re
from frappe import _
from frappe.utils import getdate, cstr, flt, date_diff, cint, get_link_to_form

@frappe.whitelist()
def get_gl_data(from_date,to_date,company,account, get_opening_closing_data):
    # Opening Balance
    gl_opening_entries = frappe.db.sql("""
        select sum(debit-credit) as balance
        from `tabGL Entry`
        where company = '{company}' and account = '{account}' and posting_date < '{from_date}' AND is_cancelled=0
    """.format(company=company,account=account,from_date=from_date))

    date_wise_balance = []

    if gl_opening_entries:
        previous_balance = gl_opening_entries[0][0] or 0.0
    else:
        previous_balance = 0.0

    previous_date = from_date

    gl_entries = frappe.db.sql("""
        select debit, credit, posting_date
        from `tabGL Entry`
        where company = '{company}' and account = '{account}' and posting_date BETWEEN '{from_date}' AND '{to_date}' AND is_cancelled=0
        order by posting_date asc    
    """.format(company=company,account=account,from_date=from_date,to_date=to_date),as_dict=1)

    for idx,gl in enumerate(gl_entries):
        day_diff = date_diff(gl.posting_date,previous_date)
        if day_diff == 0:
            previous_date = gl.posting_date
            previous_balance += flt(gl.debit - gl.credit)
        elif day_diff > 0:      
            date_wise_balance.append({"date":previous_date,"balance":previous_balance, "days":day_diff})
            previous_date = gl.posting_date
            previous_balance += flt(gl.debit - gl.credit)         

        if idx == len(gl_entries) - 1:
            day_diff = date_diff(to_date,previous_date)
            date_wise_balance.append({"date":previous_date,"balance":previous_balance, "days":day_diff})

    if not date_wise_balance and previous_balance:
        day_diff = date_diff(to_date, from_date)
        date_wise_balance.append({"date":previous_date, "balance":previous_balance, "days":day_diff})

    return date_wise_balance

@frappe.whitelist()
def create_item(doc_name):
    if not cint(frappe.db.get_value("Accounts Settings","Accounts Settings","enable_expense_item_creation")) == 1:
        frappe.throw("Please Enable 'Create Item on Creation of Expense Account' in 'Accounts Settings'")
    self = frappe.get_doc("Account",doc_name)
    if self.account_type == "Expense Account" and cint(frappe.db.get_value("Accounts Settings","Accounts Settings","enable_expense_item_creation")) == 1:
        if not frappe.db.exists("Item Group","Expense Accounts"):
            item_group = frappe.new_doc("Item Group")
            item_group.item_group_name = "Expense Accounts"
            item_group.parent_item_group = "All Item Groups"
            item_group.is_group = 1
            item_group.save(ignore_permissions=True)
  
        if not frappe.db.exists("Item",self.account_name):
            item = frappe.new_doc('Item')    
            item.item_name = self.account_name
            item.item_code = self.account_name
            item.item_group = 'Expense Accounts'
            item.is_sales_item = 0
            item.is_purchase_item = 1
            item.has_batch_no = 0
            item.has_serial_no = 0
            item.is_stock_item = 0
            item.maintain_as_is_stock = 0
            item.include_item_in_manufacturing = 0
            item.append('item_defaults',{
                "company":self.company,
                "expense_account":self.name
            })
            item.save(ignore_permissions=True)

            item_doc_name = frappe.bold(get_link_to_form(item.doctype, item.name))

            return "Item {} Has been Created".format(item_doc_name)

    



