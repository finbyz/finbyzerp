from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice as _PurchaseInvoice

class PurchaseInvoice(_PurchaseInvoice):
	def calculate_taxes_and_totals(self):
		from finbyzerp.finbyzerp.override.utils import calculate_taxes_and_totals

		calculate_taxes_and_totals(self)

		if self.doctype in (
			"Sales Order",
			"Delivery Note",
			"Sales Invoice",
			"POS Invoice",
		):
			self.calculate_commission()
			self.calculate_contribution()