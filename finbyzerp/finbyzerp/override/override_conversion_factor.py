import frappe

def validate_conversion(self, method):
    conversion_factor = frappe.db.get_single_value("Stock Settings", "calculate_conversion_factor_based_on_stock_quantity_and_quantity")
    if conversion_factor:
        for i in self.items:
            if i.qty > 0 and i.stock_uom != i.uom:
                i.conversion_factor = (i.stock_qty/i.qty)