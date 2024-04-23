from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice as _SalesInvoice

class SalesInvoice(_SalesInvoice):
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