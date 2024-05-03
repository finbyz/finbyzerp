import frappe
from frappe.utils import flt
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals as _calculate_taxes_and_totals

class calculate_taxes_and_totals(_calculate_taxes_and_totals):
	def calculate_totals(self):
		if self.doc.get("taxes"):
			self.doc.grand_total = flt(self.doc.get("taxes")[-1].total) + flt(self.doc.rounding_adjustment)
		else:
			self.doc.grand_total = flt(self.doc.net_total)

		if self.doc.get("taxes"):
			self.doc.total_taxes_and_charges = flt(
				self.doc.grand_total - self.doc.net_total - flt(self.doc.rounding_adjustment),
				self.doc.precision("total_taxes_and_charges"),
			)
		else:
			self.doc.total_taxes_and_charges = 0.0

		self._set_in_company_currency(self.doc, ["total_taxes_and_charges", "rounding_adjustment"])

		if self.doc.doctype in [
			"Quotation",
			"Sales Order",
			"Delivery Note",
			"Sales Invoice",
			"POS Invoice",
		]:
			self.doc.base_grand_total = (
				flt(self.doc.grand_total * self.doc.conversion_rate, 2)
				if self.doc.total_taxes_and_charges
				else self.doc.base_net_total
			)
		else:
			self.doc.taxes_and_charges_added = self.doc.taxes_and_charges_deducted = 0.0
			for tax in self.doc.get("taxes"):
				if tax.category in ["Valuation and Total", "Total"]:
					if tax.add_deduct_tax == "Add":
						self.doc.taxes_and_charges_added += flt(tax.tax_amount_after_discount_amount)
					else:
						self.doc.taxes_and_charges_deducted += flt(tax.tax_amount_after_discount_amount)

			self.doc.round_floats_in(self.doc, ["taxes_and_charges_added", "taxes_and_charges_deducted"])

			self.doc.base_grand_total = (
				flt(self.doc.grand_total * self.doc.conversion_rate)
				if (self.doc.taxes_and_charges_added or self.doc.taxes_and_charges_deducted)
				else self.doc.base_net_total
			)

			self._set_in_company_currency(
				self.doc, ["taxes_and_charges_added", "taxes_and_charges_deducted"]
			)

		self.doc.round_floats_in(self.doc, ["grand_total", "base_grand_total"])

		self.set_rounded_total()

	def round_off_totals(self, tax):
		if self.doc.currency == "INR":
			tax.tax_amount = round(tax.tax_amount, 2)
			tax.tax_amount_after_discount_amount = round(tax.tax_amount_after_discount_amount, 2)
		else:
			tax.tax_amount = flt(tax.tax_amount, tax.precision("tax_amount"))
			tax.tax_amount_after_discount_amount = flt(
				tax.tax_amount_after_discount_amount, tax.precision("tax_amount")
			)

		if tax.account_head in frappe.flags.round_off_applicable_accounts:
			tax.tax_amount = round(tax.tax_amount, 0)
			tax.tax_amount_after_discount_amount = round(tax.tax_amount_after_discount_amount, 0)
		

	def round_off_base_values(self, tax):
		tax.base_tax_amount = round(tax.base_tax_amount, 2)
		tax.base_tax_amount_after_discount_amount = round(tax.base_tax_amount_after_discount_amount, 2)

		# Round off to nearest integer based on regional settings
		if tax.account_head in frappe.flags.round_off_applicable_accounts:
			tax.base_tax_amount = round(tax.base_tax_amount, 0)
			tax.base_tax_amount_after_discount_amount = round(tax.base_tax_amount_after_discount_amount, 0)
	
	def calculate_net_total(self):
		self.doc.total_qty = (
			self.doc.total
		) = self.doc.base_total = self.doc.net_total = self.doc.base_net_total = 0.0

		for item in self._items:
			self.doc.total += item.amount
			self.doc.total_qty += item.qty
			self.doc.base_total += item.base_amount
			self.doc.net_total += item.net_amount
			self.doc.base_net_total += item.base_net_amount
		
		self.doc.base_net_total = flt(self.doc.base_net_total, 2)

		self.doc.round_floats_in(self.doc, ["total", "base_total", "net_total", "base_net_total"])