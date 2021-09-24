from __future__ import unicode_literals
import frappe
from frappe.utils import flt

def validate(self,method):
    update_jv_exchange_rate(self)

def update_jv_exchange_rate(self):
    set_exchange_rate = False
    if self.get('references'):
        for ref in self.get('references'):
            if ref.reference_doctype == "Journal Entry":
                exchange_rate = frappe.db.get_value("Journal Entry Account",{"parent":ref.reference_name,"party_type":self.party_type,"party":self.party},"exchange_rate")
                if exchange_rate and ref.exchange_rate != exchange_rate:
                    ref.exchange_rate = exchange_rate
                    set_exchange_rate = True
    
    if set_exchange_rate:
        self.set_tax_withholding()
        self.apply_taxes()
        self.set_amounts()
        self.clear_unallocated_reference_document_rows()
        self.validate_payment_against_negative_invoice()
        self.set_remarks()
        self.validate_allocated_amount()
        self.set_status()
