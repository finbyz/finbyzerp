from india_compliance.gst_india.constants import GST_TAX_TYPES
import frappe


def update_transaction_tax_details(self):
	tax_total_keys = tuple(f"total_{tax}_amount" for tax in GST_TAX_TYPES)

	for key in tax_total_keys:
		self.transaction_details[key] = 0
	# Finbyz Changes Start
	reverse_charge_account = frappe.db.get_value("GST Account", {'company': self.doc.company, "account_type" : "Output"}, "export_reverse_charge_account")

	reverse_charge_amount = 0
	total_tax_amount = 0

	for row in self.doc.taxes:
		if reverse_charge_account == row.account_head:
			reverse_charge_amount = row.base_tax_amount_after_discount_amount
		# Finbyz Changes End
		if not row.tax_amount or row.account_head not in self.gst_accounts:
			continue

		tax = self.gst_accounts[row.account_head][:-8]
		self.transaction_details[f"total_{tax}_amount"] = abs(
			self.rounded(row.base_tax_amount_after_discount_amount)
		)
		total_tax_amount += self.transaction_details[f"total_{tax}_amount"]

	# Other Charges
	current_total = 0
	for key in ("total", "rounding_adjustment", *tax_total_keys):
		current_total += self.transaction_details.get(key)

	current_total -= self.transaction_details.discount_amount
	other_charges = self.transaction_details.grand_total - current_total

	if reverse_charge_amount < 0 and other_charges < 0:
		other_charges = round(other_charges, 1) - round(reverse_charge_amount, 1)
		self.transaction_details.grand_total += total_tax_amount

	if 0 > other_charges > -0.1:
		# other charges cannot be negative
		# handle cases where user has higher precision than 2
		self.transaction_details.rounding_adjustment = self.rounded(
			self.transaction_details.rounding_adjustment + other_charges
		)
	else:
		self.transaction_details.other_charges = self.rounded(other_charges)