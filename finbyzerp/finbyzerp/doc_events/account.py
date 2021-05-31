from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, cstr, flt, date_diff

@frappe.whitelist()
def get_gl_data(from_date,to_date,company,account):
    # Opening Balance
    gl_opening_entries = frappe.db.sql("""
        select sum(debit-credit) as balance
        from `tabGL Entry`
        where company = '{company}' and account = '{account}' and posting_date < '{from_date}'
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
        where company = '{company}' and account = '{account}' and posting_date BETWEEN '{from_date}' AND '{to_date}'
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

        if idx == len(gl_entries)-1:
            day_diff = date_diff(to_date,previous_date)
            date_wise_balance.append({"date":previous_date,"balance":previous_balance, "days":day_diff})
            
    return date_wise_balance
