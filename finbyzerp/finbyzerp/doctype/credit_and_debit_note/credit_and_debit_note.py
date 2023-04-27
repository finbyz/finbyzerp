# Copyright (c) 2021, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe, json
from frappe.model.document import Document
from frappe.utils import nowdate,get_url_to_form
from frappe import _
from erpnext.controllers.accounts_controller import get_taxes_and_charges
from frappe.utils import flt,cint,round_based_on_smallest_currency_fraction
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
from erpnext.stock.get_item_details import get_item_tax_map
from frappe.model.mapper import get_mapped_doc
from erpnext.controllers.accounts_controller import AccountsController

# from erpnext.controllers.accounts_controller import is_rounded_total_disabled

@frappe.whitelist()
def check_is_return(self):
	if self.type=="Credit Note" and self.party_type=="Supplier":
		self.is_return = 0
	elif self.type=="Debit Note" and self.party_type=="Customer":
		self.is_return = 0
	else:
		self.is_return = 1

class CreditandDebitNote(Document):
	def before_naming(self):
		if self.type=="Credit Note":
			self.naming_series="CR-.fiscal.-"
		else:
			self.naming_series="DR-.fiscal.-"
		

	@frappe.whitelist()
	def validate(self):
		self.check_is_return()
		self.set_return_qty()
		self.get_item_code()
		self.calculate_debit_credit_taxes()
	
	def get_item_code(self):
		for row in self.items:
			row.item_name = "Credit Note" if self.type == "Credit Note" else "Debit Note"
			if not frappe.db.exists("Item",row.item_name):
				doc=frappe.new_doc("Item")
				doc.item_code=row.item_name
				doc.item_group="All Item Groups"
				doc.save()
			row.item_code=frappe.db.get_value("Item",row.item_name,"item_code")

	def on_submit(self):
		self.create_debit_credit_entry()

	def on_cancel(self):
		self.cancel_debit_credit_entry()
	
	def check_is_return(self):
		if self.type=="Credit Note" and self.party_type=="Supplier":
			self.is_return = 0
		elif self.type=="Debit Note" and self.party_type=="Customer":
			self.is_return = 0
		else:
			self.is_return = 1

	@frappe.whitelist()
	def set_return_qty(self):
		for item in self.items:
			# item.qty = abs(item.qty)
			# if self.is_return:
			# 	item.qty = -(item.qty)

			# if self.party_type == "Supplier":
			# 	item.received_qty=abs(item.received_qty)
			# 	item.stock_qty=abs(item.stock_qty)
			# 	if self.is_return:
			# 		item.received_qty = -(abs(item.received_qty))
			# 		item.stock_qty = -(abs(item.stock_qty))

			item.item_name = "Credit Note" if self.type == "Credit Note" else "Debit Note"
			if item.get("item_tax_template"):
				item.item_tax_rate = get_item_tax_map(self.get('company'), item.item_tax_template, as_json=True)
			else:
				item.item_tax_rate='{}'
			
	@frappe.whitelist()
	def calculate_debit_credit_taxes(self):
		sales = 1 if self.party_type == "Customer" else 0
		self.taxes = self.sales_taxes if sales == 1 else self.purchase_taxes
		self.taxes_and_charges = self.sales_taxes_and_charges if sales == 1 else self.purchase_taxes_and_charges
		self.doc = self
		self.discount_amount_applied = False
		self._items = self.items

		frappe.flags.round_off_applicable_accounts = []
		calculate_taxes_and_totals.validate_conversion_rate(self)
		calculate_taxes_and_totals.calculate_item_values(self)
		calculate_taxes_and_totals.validate_item_tax_template(self)
		calculate_taxes_and_totals.initialize_taxes(self)
		self.determine_exclusive_rate()
		calculate_taxes_and_totals.calculate_net_total(self)
		calculate_taxes_and_totals.calculate_taxes(self)

		if sales == 1:
			self.sales_taxes_and_charges = self.taxes_and_charges
			self.sales_taxes = self.taxes
		else:
			self.purchase_taxes_and_charges = self.taxes_and_charges
			self.purchase_taxes = self.taxes			
		calculate_taxes_and_totals.manipulate_grand_total_for_inclusive_tax(self)
		self.calculate_totals()


	def determine_exclusive_rate(self):
		if not any(cint(tax.included_in_print_rate) for tax in self.doc.get("taxes")):
			return

		for item in self._items:
			item_tax_map = self._load_item_tax_rate(item.item_tax_rate)
			cumulated_tax_fraction = 0
			total_inclusive_tax_amount_per_qty = 0
			for i, tax in enumerate(self.doc.get("taxes")):
				(
					tax.tax_fraction_for_current_item,
					inclusive_tax_amount_per_qty,
				) = self.get_current_tax_fraction(tax, item_tax_map)

				if i == 0:
					tax.grand_total_fraction_for_current_item = 1 + tax.tax_fraction_for_current_item
				else:
					tax.grand_total_fraction_for_current_item = (
						self.doc.get("taxes")[i - 1].grand_total_fraction_for_current_item
						+ tax.tax_fraction_for_current_item
					)

				cumulated_tax_fraction += tax.tax_fraction_for_current_item
				total_inclusive_tax_amount_per_qty += inclusive_tax_amount_per_qty * flt(item.qty)

			if (
				not self.discount_amount_applied
				and item.qty
				and (cumulated_tax_fraction or total_inclusive_tax_amount_per_qty)
			):
				amount = flt(item.amount) - total_inclusive_tax_amount_per_qty

				item.net_amount = flt(amount / (1 + cumulated_tax_fraction))
				item.net_rate = flt(item.net_amount / item.qty, item.precision("net_rate"))
				item.discount_percentage = flt(item.discount_percentage, item.precision("discount_percentage"))

				self._set_in_company_currency(item, ["net_rate", "net_amount"])
	
	def _load_item_tax_rate(self, item_tax_rate):
		return json.loads(item_tax_rate) if item_tax_rate else {}


	def get_current_tax_fraction(self, tax, item_tax_map):
		"""
		Get tax fraction for calculating tax exclusive amount
		from tax inclusive amount
		"""
		current_tax_fraction = 0
		inclusive_tax_amount_per_qty = 0

		if cint(tax.included_in_print_rate):
			tax_rate = self._get_tax_rate(tax, item_tax_map)

			if tax.charge_type == "On Net Total":
				current_tax_fraction = tax_rate / 100.0

			elif tax.charge_type == "On Previous Row Amount":
				current_tax_fraction = (tax_rate / 100.0) * self.doc.get("taxes")[
					cint(tax.row_id) - 1
				].tax_fraction_for_current_item

			elif tax.charge_type == "On Previous Row Total":
				current_tax_fraction = (tax_rate / 100.0) * self.doc.get("taxes")[
					cint(tax.row_id) - 1
				].grand_total_fraction_for_current_item

			elif tax.charge_type == "On Item Quantity":
				inclusive_tax_amount_per_qty = flt(tax_rate)

		if getattr(tax, "add_deduct_tax", None) and tax.add_deduct_tax == "Deduct":
			current_tax_fraction *= -1.0
			inclusive_tax_amount_per_qty *= -1.0

		return current_tax_fraction, inclusive_tax_amount_per_qty

	def _get_tax_rate(self, tax, item_tax_map):
		if tax.account_head in item_tax_map:
			return flt(item_tax_map.get(tax.account_head), self.doc.precision("rate", tax))
		else:
			return tax.rate

	def _set_in_company_currency(self, doc, fields):
		"""set values in base currency"""
		for f in fields:
			val = flt(
				flt(doc.get(f), doc.precision(f)) * self.doc.conversion_rate, doc.precision("base_" + f)
			)
			doc.set("base_" + f, val)

# Create Purchase Or Sales Invoice Entry based on customer and supplier.
	def create_debit_credit_entry(self):
		def get_entry(source_name,target_doc=None):
			source_doc = frappe.get_doc("Credit and Debit Note",source_name)
			target_doctype = "Sales Invoice" if source_doc.party_type == "Customer" else "Purchase Invoice"
			if target_doctype == "Sales Invoice":
				target_item_doctype = "Sales Invoice Item"
				target_tax_doctype = "Sales Taxes and Charges"
			else:
				target_item_doctype = "Purchase Invoice Item"
				target_tax_doctype = "Purchase Taxes and Charges"

			def set_missing_values(source, target):
				target.is_return=source.is_return
				if source.set_posting_time:
					target.set_posting_time=1
					target.posting_time=source.posting_time
					target.posting_date=source.posting_date
				if target_doctype == "Sales Invoice":
					target.is_consolidated=0
					target.customer = source.party
					target.naming_series="SI-CR-.fiscal.-.###" if source.type=="Credit Note" else 'SI-DR-.fiscal.-.###'
				else:
					target.supplier = source.party
					target.naming_series=' PI-DR-.fiscal.-.###' if source.type=="Debit Note" else "PI-CR-.fiscal.-.###"
				target.remarks = source.remarks
				target.series_value = source.series_value
				target.run_method("set_missing_values")
				target.run_method("calculate_taxes_and_totals")
				for row in source.items:
					row.item_code=frappe.db.get_value("Item",row.item_name,"item_code")
				
			def update_item(source,target,source_parent):
				if not frappe.db.exists("Item",target.item_name):
					doc=frappe.new_doc("Item")
					doc.item_code=target.item_name
					doc.item_group="All Item Groups"
					doc.save()
				target.item_code=frappe.db.get_value("Item",target.item_name,"item_code")
				# frappe.throw(str(target.item_code))
				target.uom = frappe.db.get_value("Stock Settings",None,"stock_uom")
				target.description = source.item_name
				target.concentration = 100
				target.update_stock = 0
				target.conversion_factor = 1
				if source_parent.is_return:
					target.quantity = -(target.quantity)
					target.qty = -(target.qty)	
				if target_doctype == "Purchase Invoice":
					if source_parent.is_return:
						target.received_qty = -(target.received_qty)
						target.stock_qty = -(target.stock_qty)
				if target_doctype == "Sales Invoice":
					target.income_account = frappe.db.get_value("Company",source_parent.company,"default_income_account")
				target.income_account=source.income_account
				target.expense_account=source.expense_account

			doclist = get_mapped_doc(source_doc.doctype, source_doc.name, {
				source_doc.doctype: {
					"doctype": target_doctype,
				},
				"Credit and Debit Note Item": {
					"doctype": target_item_doctype,
					"field_map": [
						["qty","quantity"],
						["rate","price"],
					],
					"postprocess": update_item
				},
				target_tax_doctype: {
					"doctype": target_tax_doctype,
				},
			}, target_doc, set_missing_values)

			return doclist

		return_entry = get_entry(self.name)
		try:
			return_entry.flags.ignore_permissions = True
			return_entry.save()
			return_entry.taxes_and_charges=self.get('sales_taxes_and_charges') if self.party_type == "Customer" else  self.get('purchase_taxes_and_charges')
			return_entry.tax_category=None
			submit=0
			if not cint(frappe.db.get_single_value("GST Settings", "enable_api")):
				submit=1
			else:
				if not frappe.db.get_value("E Invoice User", {"company": self.get("company")}):
					submit=1
			if (submit and return_entry.doctype == "Sales Invoice") or return_entry.doctype == "Purchase Invoice":
				return_entry.submit()
			state="submitted" if submit else "Created"
			if return_entry.doctype == "Sales Invoice":
				self.db_set('si_ref',return_entry.name)
				self.db_set('pi_ref',None)
				url = get_url_to_form("Sales Invoice",return_entry.name)
				frappe.msgprint(_("Sales Invoice <b><a href='{url}'>{name}</a></b> has been {state}!".format(url=url, name=return_entry.name,state=state)), title="Sales Invoice "+str(state), indicator="green")
			else:
				self.db_set('pi_ref',return_entry.name)
				self.db_set('si_ref',None)
				url = get_url_to_form("Purchase Invoice",return_entry.name)
				frappe.msgprint(_("Purchase Invoice <b><a href='{url}'>{name}</a></b> has been {state}!".format(url=url, name=return_entry.name,state=state)), title="Purchase Invoice "+str(state), indicator="green")

		except Exception as e:
			frappe.throw(_(str(e)))

	# Cancel and delete created purchase or sales invoice entry
	def cancel_debit_credit_entry(self):
		if self.party_type=="Customer":
			ref=self.si_ref
			ref_type="si_ref"
			doctype="Sales Invoice"
			frappe.db.set_value("Credit and Debit Note",self.name,"si_ref",'')
			self.si_ref=''
		else:
			ref=self.pi_ref
			ref_type="pi_ref"
			doctype="Purchase Invoice"
			frappe.db.set_value("Credit and Debit Note",self.name,"pi_ref",'')
			self.pi_ref=''
		if ref:
			doc=frappe.get_doc(doctype,ref)
			try:
				if doc.docstatus == 1:
					doc.cancel()
				doc.delete()
				frappe.msgprint(_("{doctype} has been deleted!".format(doctype=doctype)), title="{} Deleted".format(doctype), indicator="green")
			except Exception as e:
				frappe.db.set_value("Credit and Debit Note",self.name,ref_type,ref)
				frappe.throw(_(str(e)))


	def _load_item_tax_rate(self, item_tax_rate):
		return json.loads(item_tax_rate) if item_tax_rate else {}

	def get_current_tax_amount(self, item, tax, item_tax_map):
		tax_rate = self._get_tax_rate(tax, item_tax_map)
		current_tax_amount = 0.0

		if tax.charge_type == "Actual":
			# distribute the tax amount proportionally to each item row
			actual = flt(tax.tax_amount, tax.precision("tax_amount"))
			current_tax_amount = item.net_amount*actual / self.doc.net_total if self.doc.net_total else 0.0

		elif tax.charge_type == "On Net Total":
			current_tax_amount = (tax_rate / 100.0) * item.net_amount
		elif tax.charge_type == "On Previous Row Amount":
			current_tax_amount = (tax_rate / 100.0) * \
				self.doc.get("taxes")[cint(tax.row_id) - 1].tax_amount_for_current_item
		elif tax.charge_type == "On Previous Row Total":
			current_tax_amount = (tax_rate / 100.0) * \
				self.doc.get("taxes")[cint(tax.row_id) - 1].grand_total_for_current_item
		elif tax.charge_type == "On Item Quantity":
			current_tax_amount = tax_rate * item.qty

		if not (self.doc.get("is_consolidated") or tax.get("dont_recompute_tax")):
			self.set_item_wise_tax(item, tax, tax_rate, current_tax_amount)

		return current_tax_amount

	def _get_tax_rate(self, tax, item_tax_map):
		if tax.account_head in item_tax_map:
			return flt(item_tax_map.get(tax.account_head), self.doc.precision("rate", tax))
		else:
			return tax.rate

	def set_item_wise_tax(self, item, tax, tax_rate, current_tax_amount):
		# store tax breakup for each item
		key = item.item_code or item.item_name
		item_wise_tax_amount = flt(current_tax_amount*self.doc.conversion_rate,4)
		if tax.item_wise_tax_detail.get(key):
			item_wise_tax_amount += tax.item_wise_tax_detail[key][1]

		tax.item_wise_tax_detail[key] = [tax_rate,flt(item_wise_tax_amount)]

	def get_tax_amount_if_for_valuation_or_deduction(self, tax_amount, tax):
		# if just for valuation, do not add the tax amount in total
		# if tax/charges is for deduction, multiply by -1
		if getattr(tax, "category", None):
			tax_amount = 0.0 if (tax.category == "Valuation") else tax_amount
			if self.doc.doctype in ["Purchase Order", "Purchase Invoice", "Purchase Receipt", "Supplier Quotation"] or self.party_type == "Supplier":
				tax_amount *= -1.0 if (tax.add_deduct_tax == "Deduct") else 1.0
		return tax_amount

	def round_off_totals(self, tax):
		if tax.account_head in frappe.flags.round_off_applicable_accounts:
			tax.tax_amount = round(tax.tax_amount, 0)
			tax.tax_amount_after_discount_amount = round(tax.tax_amount_after_discount_amount, 0)

		tax.tax_amount = flt(tax.tax_amount, tax.precision("tax_amount"))
		tax.tax_amount_after_discount_amount = flt(tax.tax_amount_after_discount_amount,
			tax.precision("tax_amount"))

	def _set_in_company_currency(self, doc, fields):
		"""set values in base currency"""
		for f in fields:
			val = flt(flt(doc.get(f), doc.precision(f)) * flt(self.doc.conversion_rate), doc.precision("base_" + f))
			doc.set("base_" + f, val)


	def round_off_base_values(self, tax):
		# Round off to nearest integer based on regional settings
		if tax.account_head in frappe.flags.round_off_applicable_accounts:
			tax.base_tax_amount = round(tax.base_tax_amount, 0)
			tax.base_tax_amount_after_discount_amount = round(tax.base_tax_amount_after_discount_amount, 0)

	def set_cumulative_total(self, row_idx, tax):
		tax_amount = tax.tax_amount_after_discount_amount
		tax_amount = self.get_tax_amount_if_for_valuation_or_deduction(tax_amount, tax)

		if row_idx == 0:
			tax.total = flt(self.doc.net_total + tax_amount, tax.precision("total"))
		else:
			tax.total = flt(self.doc.get("taxes")[row_idx-1].total + tax_amount, tax.precision("total"))

	def set_rounded_total(self):
		if self.doc.meta.get_field("rounded_total"):
			if AccountsController.is_rounded_total_disabled(self.doc):
				self.doc.rounded_total = self.doc.base_rounded_total = 0
				return

			self.doc.rounded_total = round_based_on_smallest_currency_fraction(self.doc.grand_total,
				self.doc.currency, self.doc.precision("rounded_total"))

			#if print_in_rate is set, we would have already calculated rounding adjustment
			self.doc.rounding_adjustment += flt(self.doc.rounded_total - self.doc.grand_total,
				self.doc.precision("rounding_adjustment"))

			self._set_in_company_currency(self.doc, ["rounding_adjustment", "rounded_total"])

	def calculate_totals(self):
		self.doc.grand_total = flt(self.doc.get("taxes")[-1].total) + flt(self.doc.rounding_adjustment) \
			if self.doc.get("taxes") else flt(self.doc.net_total)

		self.doc.total_taxes_and_charges = flt(self.doc.grand_total - self.doc.net_total
			- flt(self.doc.rounding_adjustment), self.doc.precision("total_taxes_and_charges"))

		self._set_in_company_currency(self.doc, ["total_taxes_and_charges", "rounding_adjustment"])

		if self.doc.doctype in ["Quotation", "Sales Order", "Delivery Note", "Sales Invoice", "POS Invoice"] or self.doc.party_type == "Customer":
			self.doc.base_grand_total = flt(self.doc.grand_total * self.doc.conversion_rate, self.doc.precision("base_grand_total")) \
				if self.doc.total_taxes_and_charges else self.doc.base_net_total
		else:
			self.doc.taxes_and_charges_added = self.doc.taxes_and_charges_deducted = 0.0
			for tax in self.doc.get("taxes"):
				if tax.category in ["Valuation and Total", "Total"]:
					if tax.add_deduct_tax == "Add":
						self.doc.taxes_and_charges_added += flt(tax.tax_amount_after_discount_amount)
					else:
						self.doc.taxes_and_charges_deducted += flt(tax.tax_amount_after_discount_amount)

			self.doc.round_floats_in(self.doc, ["taxes_and_charges_added", "taxes_and_charges_deducted"])

			self.doc.base_grand_total = flt(self.doc.grand_total * flt(self.doc.conversion_rate)) \
				if (self.doc.taxes_and_charges_added or self.doc.taxes_and_charges_deducted) \
				else self.doc.base_net_total

			self._set_in_company_currency(self.doc,
				["taxes_and_charges_added", "taxes_and_charges_deducted"])

		self.doc.round_floats_in(self.doc, ["grand_total", "base_grand_total"])

		self.set_rounded_total()