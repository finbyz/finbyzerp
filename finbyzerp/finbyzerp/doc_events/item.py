import frappe

def validate(self,method):
    before_validate(self,method)
    if self.is_new() and not self.is_stock_item:
        frappe.msgprint("Please define correct expense account in Item Defaults.<br>In absence of same expense will be parked in 'Cost of Goods Sold' account")

def before_validate(self,method):
    if "'" in self.item_code or '"' in self.item_code:
        frappe.throw(""" Item Code not allowed with any special Characters like " or ' """)