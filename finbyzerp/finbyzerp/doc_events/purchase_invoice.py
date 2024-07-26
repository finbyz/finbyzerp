import frappe
def pi_validate(self,method):
    set_account_in_transaction(self)


def set_account_in_transaction(self):
    if self.doctype == "Sales Invoice":
        party_type = "Customer"
        party = self.customer
        account_type = "Receivable"
        field = 'debit_to'
    else:
        party_type = "Supplier"
        party = self.supplier
        account_type = "Payable"
        field = 'credit_to'

    if not frappe.db.exists("GL Entry",{'party_type':party_type,'party':party}):
        if field:
            if frappe.db.get_value("Account",field,'account_currency') != self.currency:
                if frappe.db.exists("Account",{'account_type':account_type,'freeze_account':'No','company':self.company,'account_currency':self.currency}):
                    field = frappe.db.get_value("Account",{'account_type':account_type,'freeze_account':'No','company':self.company,'account_currency':self.currency})
                else:
                    frappe.msgprint("Please create {0} account in {1} for company {2} and set in accounting detail".format(account_type,self.currency,self.company))

