import frappe
from frappe import _
from frappe.utils import flt
from frappe import _, scrub
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions


def make_invoices(self):
	names = []
	mandatory_error_msg = _("Row {0}: {1} is required to create the Opening {2} Invoices")
	if not self.company:
		frappe.throw(_("Please select the Company"))

	for row in self.invoices:
		if not row.qty:
			row.qty = 1.0

		# always mandatory fields for the invoices
		if not row.temporary_opening_account:
			row.temporary_opening_account = get_temporary_opening_account(self.company)
		row.party_type = "Customer" if self.invoice_type == "Sales" else "Supplier"

		# Allow to create invoice even if no party present in customer or supplier.
		if not frappe.db.exists(row.party_type, row.party):
			if self.create_missing_party:
				self.add_party(row.party_type, row.party)
			else:
				frappe.throw(_("{0} {1} does not exist.").format(frappe.bold(row.party_type), frappe.bold(row.party)))

		if not row.item_name:
			row.item_name = _("Opening Invoice Item")
		if not row.posting_date:
			row.posting_date = nowdate()
		if not row.due_date:
			row.due_date = nowdate()

		for d in ("Party", "Outstanding Amount", "Temporary Opening Account"):
			if not row.get(scrub(d)):
				frappe.throw(mandatory_error_msg.format(row.idx, _(d), self.invoice_type))

		args = self.get_invoice_dict(row=row)
		if not args:
			continue

		if row.outstanding_amount < 0:
			doc = frappe.new_doc("Journal Entry")
			doc.naming_series = 'O' + doc.naming_series
			doc.voucher_type = "Credit Note" if self.invoice_type == 'Sales' else "Debit Note"
			doc.posting_date = row.posting_date
			doc.company = self.company
			doc.is_opening = 'Yes'
			if row.exchange_rate:
				doc.multi_currency = 1
			if self.invoice_type == 'Sales':
				doc.append('accounts', {
					'account': row.account or frappe.get_value("Company", doc.company, 'default_receivable_account'),
					'party_type': 'Customer',
					'party': row.party,
					'debit_in_account_currency': 0,
					'credit_in_account_currency': abs(row.outstanding_amount),
					'is_advance': 'Yes',
					"cost_center":row.cost_center,
					"exchange_rate":row.exchange_rate or 1
				})

				doc.append('accounts', {
					'account': row.temporary_opening_account,
					'party_type': None,
					'party': None,
					'debit_in_account_currency': abs(row.outstanding_amount) * (row.exchange_rate or 1),
					'credit_in_account_currency': 0,
					"cost_center":row.cost_center
				})
			
			elif self.invoice_type == 'Purchase':
				doc.append('accounts', {
					'account': row.account or frappe.get_value("Company", doc.company, 'default_payable_account'),
					'party_type': 'Supplier',
					'party': row.party,
					'debit_in_account_currency': abs(row.outstanding_amount),
					'credit_in_account_currency': 0,
					'is_advance': 'Yes',
					"cost_center":row.cost_center,
					"exchange_rate":row.exchange_rate or 1
				})

				doc.append('accounts', {
					'account': row.temporary_opening_account,
					'party_type': None,
					'party': None,
					'debit_in_account_currency': 0,
					'credit_in_account_currency': abs(row.outstanding_amount) * (row.exchange_rate or 1),
					"cost_center":row.cost_center
				})

			doc.save()
			doc.submit()
			names.append(doc.name)
		elif row.outstanding_amount > 0:
			doc = frappe.get_doc(args).insert()
			doc.submit()
			names.append(doc.name)

		if len(self.invoices) > 5:
			frappe.publish_realtime(
				"progress", dict(
					progress=[row.idx, len(self.invoices)],
					title=_('Creating {0}').format(doc.doctype)
				),
				user=frappe.session.user
			)

	return names

def get_invoice_dict(self, row=None):
	def get_item_dict():
		default_uom = frappe.db.get_single_value("Stock Settings", "stock_uom") or _("Nos")
		cost_center = row.get('cost_center') or frappe.get_cached_value('Company',
			self.company,  "cost_center")

		if not cost_center:
			frappe.throw(
				_("Please set the Default Cost Center in {0} company.").format(frappe.bold(self.company))
			)
		
		row.outstanding_amount = flt(row.outstanding_amount)
		row.qty = flt(row.qty)
		rate = flt(row.outstanding_amount) / flt(row.qty)

		return frappe._dict({
			"uom": default_uom,
			"rate": rate or 0.0,
			"price":rate or 0.0,
			"qty": row.qty,
			"quantity":row.qty,
			"conversion_factor": 1.0,
			"item_name": row.item_name or "Opening Invoice Item",
			"description": row.item_name or "Opening Invoice Item",
			income_expense_account_field: row.temporary_opening_account,
			"cost_center": cost_center
		})

	if not row:
		return None

	party_type = "Customer"
	income_expense_account_field = "income_account"
	account_field = "debit_to"
	if self.invoice_type == "Purchase":
		party_type = "Supplier"
		income_expense_account_field = "expense_account"
		account_field = "credit_to"

	item = get_item_dict()

	args = frappe._dict({
		"items": [item],
		"is_opening": "Yes",
		"set_posting_time": 1,
		"company": self.company,
		"cost_center": self.cost_center,
		"due_date": row.due_date,
		"posting_date": row.posting_date,
		frappe.scrub(party_type): row.party,
		"doctype": "Sales Invoice" if self.invoice_type == "Sales" else "Purchase Invoice",
		"currency": row.currency or frappe.get_cached_value('Company',  self.company,  "default_currency"),
		"conversion_rate": row.exchange_rate,
		account_field: row.account
	})

	# accounting_dimension = get_accounting_dimensions()

	# for dimension in accounting_dimension:
	# 	args.update({
	# 		dimension: item.get(dimension)
	# 	})

	if self.invoice_type == "Sales":
		args["is_pos"] = 0
		args['invoice_no'] = row.invoice_no
	else:
		args['bill_no'] = row.invoice_no

	return args

@frappe.whitelist()
def get_temporary_opening_account(company=None):
	if not company:
		return

	accounts = frappe.get_all("Account", filters={
		'company': company,
		'account_type': 'Temporary'
	})
	if not accounts:
		frappe.throw(_("Please add a Temporary Opening account in Chart of Accounts"))

	return accounts[0].name

@frappe.whitelist()
def get_account_currency(party,company,invoice_type):
	account = frappe.db.get_value("Party Account",{"parent":party,"company":company},"account")
	if not account:
		act_type = "default_receivable_account" if invoice_type == "Sales" else "default_payable_account"
		account = frappe.db.get_value("Company",company,act_type)
	currency = frappe.db.get_value("Account",account,"account_currency")
	return {"account":account,"currency":currency}
