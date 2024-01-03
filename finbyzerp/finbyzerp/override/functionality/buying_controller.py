import frappe
from frappe.utils import flt


def set_qty_as_per_stock_uom(self):
	conversion_factor = frappe.db.get_single_value("Stock Settings", "calculate_conversion_factor_based_on_stock_quantity_and_quantity")
	for d in self.get("items"):
		if d.meta.get_field("stock_qty"):
			# Check if item code is present
			# Conversion factor should not be mandatory for non itemized items
			if not d.conversion_factor and d.item_code:
				frappe.throw(_("Row {0}: Conversion Factor is mandatory").format(d.idx))
			if conversion_factor == 0:
				d.stock_qty = flt(d.qty) * flt(d.conversion_factor)

				if self.doctype == "Purchase Receipt" and d.meta.get_field("received_stock_qty"):
					# Set Received Qty in Stock UOM
					d.received_stock_qty = flt(d.received_qty) * flt(
						d.conversion_factor, d.precision("conversion_factor")
					)
