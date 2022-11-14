import frappe

def validate(self,method):
    update_invoice_warehouse(self)

def update_invoice_warehouse(self):
    for each_item in self.items:
        if each_item.get("against_sales_invoice") and each_item.get("si_detail"):
            filters={"parent":each_item.get("against_sales_invoice"),"name":each_item.get("si_detail")}
            if frappe.db.get_value("Sales Invoice Item",filters,'warehouse') != each_item.warehouse:
                frappe.db.set_value("Sales Invoice Item",filters,'warehouse',each_item.warehouse)
