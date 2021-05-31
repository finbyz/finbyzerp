import frappe

def validate(self,method):
    if self.is_new() and not self.is_stock_item:
        frappe.msgprint("Please define correct expense account in Item Defaults.<br>In absence of same expense will be parked in 'Cost of Goods Sold' account")