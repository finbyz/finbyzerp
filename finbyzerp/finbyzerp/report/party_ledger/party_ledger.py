# Copyright (c) 2013, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from collections import OrderedDict

import frappe
from frappe import _, _dict
from frappe.utils import cstr, getdate
from six import iteritems

from erpnext import get_company_currency, get_default_company
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
	get_dimension_with_children,
)
from erpnext.accounts.report.financial_statements import get_additional_conditions, get_cost_centers_with_children
from erpnext.accounts.report.utils import convert_to_presentation_currency, get_currency
from erpnext.accounts.utils import get_account_currency

# to cache translations
TRANSLATIONS = frappe._dict()


def execute(filters=None):
	if not filters:
		return [], []

	account_details = {}

	if filters and filters.get("print_in_account_currency") and not filters.get("account"):
		frappe.throw(_("Select an account to print in account currency"))

	for acc in frappe.db.sql("""select name, is_group from tabAccount""", as_dict=1):
		account_details.setdefault(acc.name, acc)

	if filters.get("party"):
		filters.party = frappe.parse_json(filters.get("party"))

	validate_filters(filters, account_details)

	validate_party(filters)

	filters = set_account_currency(filters)

	columns = get_columns(filters)

	update_translations()

	res = get_result(filters, account_details)

	return columns, res


def update_translations():
	TRANSLATIONS.update(
		dict(OPENING=_("Opening"), TOTAL=_("Total"), CLOSING_TOTAL=_("Closing (Opening + Total)"))
	)


def validate_filters(filters, account_details):
	if not filters.get("company"):
		frappe.throw(_("{0} is mandatory").format(_("Company")))

	if not filters.get("from_date") and not filters.get("to_date"):
		frappe.throw(
			_("{0} and {1} are mandatory").format(frappe.bold(_("From Date")), frappe.bold(_("To Date")))
		)

	if filters.get("account"):
		filters.account = frappe.parse_json(filters.get("account"))
		for account in filters.account:
			if not account_details.get(account):
				frappe.throw(_("Account {0} does not exists").format(account))

	if filters.get("account") and filters.get("group_by") == "Group by Account":
		filters.account = frappe.parse_json(filters.get("account"))
		for account in filters.account:
			if account_details[account].is_group == 0:
				frappe.throw(_("Can not filter based on Child Account, if grouped by Account"))

	if filters.get("voucher_no") and filters.get("group_by") in ["Group by Voucher"]:
		frappe.throw(_("Can not filter based on Voucher No, if grouped by Voucher"))

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

	if filters.get("project"):
		filters.project = frappe.parse_json(filters.get("project"))

	if filters.get("cost_center"):
		filters.cost_center = frappe.parse_json(filters.get("cost_center"))


def validate_party(filters):
	party_type, party = filters.get("party_type"), filters.get("party")

	if party:
		if not party_type:
			frappe.throw(_("To filter based on Party, select Party Type first"))
		else:
			for d in party:
				if not frappe.db.exists(party_type, d):
					frappe.throw(_("Invalid {0}: {1}").format(party_type, d))


def set_account_currency(filters):
	if filters.get("account") or (filters.get("party") and len(filters.party) == 1):
		filters["company_currency"] = frappe.get_cached_value(
			"Company", filters.company, "default_currency"
		)
		account_currency = None

		if filters.get("account"):
			if len(filters.get("account")) == 1:
				account_currency = get_account_currency(filters.account[0])
			else:
				currency = get_account_currency(filters.account[0])
				is_same_account_currency = True
				for account in filters.get("account"):
					if get_account_currency(account) != currency:
						is_same_account_currency = False
						break

				if is_same_account_currency:
					account_currency = currency
		
		elif filters.get("party"):
			gle_currency = frappe.db.get_value(
				"GL Entry",
				{"party_type": filters.party_type, "party": filters.party[0], "company": filters.company},
				"account_currency",
			)

			if gle_currency:
				account_currency = gle_currency
			else:
				account_currency = (
					None
					if filters.party_type in ["Employee", "Student", "Shareholder", "Member"]
					else frappe.db.get_value(filters.party_type, filters.party[0], "default_currency")
				)

		filters["account_currency"] = account_currency or filters.company_currency
		if filters.account_currency != filters.company_currency and not filters.presentation_currency:
			filters.presentation_currency = filters.account_currency

	return filters


def get_result(filters, account_details):
	accounting_dimensions = []
	if filters.get("include_dimensions"):
		accounting_dimensions = get_accounting_dimensions()

	gl_entries = get_gl_entries(filters, accounting_dimensions)

	data = get_data_with_opening_closing(filters, account_details, accounting_dimensions, gl_entries)

	result = get_result_as_list(data, filters)
	
	return result

def get_gl_entries(filters, accounting_dimensions):
	currency_map = get_currency(filters)
	select_fields = """, debit, credit, debit_in_account_currency,
		credit_in_account_currency """

	order_by_statement = "order by posting_date, account, creation"

	if filters.get("include_dimensions"):
		order_by_statement = "order by posting_date, creation"

	if filters.get("group_by") == "Group by Voucher":
		order_by_statement = "order by posting_date, voucher_type, voucher_no"
	if filters.get("group_by") == "Group by Account":
		order_by_statement = "order by account, posting_date, creation"

	if filters.get("include_default_book_entries"):
		filters["company_fb"] = frappe.db.get_value(
			"Company", filters.get("company"), "default_finance_book"
		)

	dimension_fields = ""
	if accounting_dimensions:
		dimension_fields = ", ".join(accounting_dimensions) + ","

	distributed_cost_center_query = ""
	if filters and filters.get("cost_center"):
		select_fields_with_percentage = """, debit*(DCC_allocation.percentage_allocation/100) as debit,
		credit*(DCC_allocation.percentage_allocation/100) as credit,
		debit_in_account_currency*(DCC_allocation.percentage_allocation/100) as debit_in_account_currency,
		credit_in_account_currency*(DCC_allocation.percentage_allocation/100) as credit_in_account_currency """

		distributed_cost_center_query = """
		UNION ALL
		SELECT name as gl_entry,
			posting_date,
			account,
			party_type,
			party,
			voucher_type,
			voucher_no, {dimension_fields}
			cost_center, project,
			against_voucher_type,
			against_voucher,
			account_currency,
			remarks, against,
			is_opening, `tabGL Entry`.creation {select_fields_with_percentage}
		FROM `tabGL Entry`,
		(
			SELECT parent, sum(percentage_allocation) as percentage_allocation
			FROM `tabDistributed Cost Center`
			WHERE cost_center IN %(cost_center)s
			AND parent NOT IN %(cost_center)s
			GROUP BY parent
		) as DCC_allocation
		WHERE company=%(company)s
		{conditions}
		AND posting_date <= %(to_date)s
		AND cost_center = DCC_allocation.parent
		""".format(
			dimension_fields=dimension_fields,
			select_fields_with_percentage=select_fields_with_percentage,
			conditions=get_conditions(filters).replace("and cost_center in %(cost_center)s ", ""),
		)

	gl_entries = frappe.db.sql(
		"""
		select
			name as gl_entry, posting_date, account, party_type, party,
			voucher_type, voucher_no, {dimension_fields}
			cost_center, project,
			against_voucher_type, against_voucher, account_currency,
			remarks, against, is_opening, creation {select_fields}
		from `tabGL Entry`
		where is_cancelled = 0 and company=%(company)s {conditions}
		{distributed_cost_center_query}
		{order_by_statement}
		""".format(
			dimension_fields=dimension_fields,
			select_fields=select_fields, 
			conditions=get_conditions(filters),
			distributed_cost_center_query=distributed_cost_center_query,
			order_by_statement=order_by_statement,
		),
		filters,
		as_dict=1,
	)
	additional_dict = {}
	additional_data = frappe.db.sql("""
		SELECT
			GROUP_CONCAT(account SEPARATOR '<br>') as accounts_list,
			GROUP_CONCAT(debit_in_account_currency SEPARATOR '<br>') as debit_list,
			GROUP_CONCAT(credit_in_account_currency SEPARATOR '<br>') as credit_list, voucher_no
		FROM
			`tabGL Entry`
		WHERE
			is_cancelled = 0 and company=%(company)s {conditions}
			{distributed_cost_center_query}
		GROUP BY voucher_no
		{order_by_statement}
	""".format(conditions=get_additional_data_conditions(filters),
			distributed_cost_center_query=distributed_cost_center_query,
			order_by_statement=order_by_statement,
		),filters, as_dict = 1)

	for row in additional_data:
		additional_dict[row.voucher_no] = {'accounts_list' : row.accounts_list, 'debit_list' : row.debit_list, 'credit_list' : row.credit_list}

	for row in gl_entries:
		if additional_dict.get(row.voucher_no):
			row['accounts_list'] = additional_dict[row.voucher_no]['accounts_list']
			row['debit_list'] = additional_dict[row.voucher_no]['debit_list']
			row['credit_list'] = additional_dict[row.voucher_no]['credit_list']
	# if filters.get('party_type') and filters.party:
	# 	list_keys = [filters.get('party_type'), filters.party]
	# 	gl_entries = list(filter(lambda d: d.party_type == filters.get('party_type') and d.party in filters.get('party'),
	# 				gl_entries))
	balance, balance_in_account_currency = 0, 0
	for index, d in enumerate(gl_entries):
		if not d.get("posting_date"):
			balance, balance_in_account_currency = 0, 0

		balance = get_balance(d, balance, "debit", "credit")
		if filters.get('party_type') and d.party_type !=filters.get('party_type'):
			gl_entries[index]  = None

		if filters.get('party') and d.party !=filters.get('party'):
			gl_entries[index]  = None

		if d.voucher_no and not d.party:
			gl_entries[index] = None
		elif d.get("accounts_list", None):
			accounts_list = d['accounts_list'].split("<br>")

			debit_list = d['debit_list'].split("<br>")
			credit_list = d['credit_list'].split("<br>")

			debit_credit_list = []
			dr_cr = []
			for i, j in zip(debit_list, credit_list):
				if float(i) > 0.0:
					dr_cr.append("Dr")
					debit_credit_list.append(format(round(float(i), 2), '.2f'))
				elif float(j) > 0.0:
					dr_cr.append("Cr")
					debit_credit_list.append(format(round(float(j), 2), '.2f'))
			
			d['debit_credit_list'] = "<style>.tbspace > tbody > tr > td{ padding: 0 2px 0 2px!important; margin:0!important; border-spacing: 0!important; }</style><table width='100%%' class='tbspace'><tbody>"
			for x, y, z in zip(accounts_list, dr_cr, debit_credit_list):
				if filters.get("print_with_description"):
					d['debit_credit_list'] += """
					<tr>
						<td width='70%%'>{}</td>
						<td>{}</td>
						<td align='right'>{}</td>
					</tr>
					""".format(x, y, z)

			d['debit_credit_list'] += "<tbody></table>"
		debit_credit_list = None
		debit_list = None
		credit_list = None
		accounts_list = None
		voucher_no = None
		party = None

	gl_entries = [i for i in gl_entries if i]

	if filters.get("presentation_currency"):
		return convert_to_presentation_currency(gl_entries, currency_map, filters.get("company"))
	else:
		return gl_entries

def get_additional_data_conditions(filters):
	conditions = []
	
	if filters.get("account"):
		filters.account = get_accounts_with_children(filters.account)
		conditions.append("account in %(account)s")

	if filters.get("cost_center"):
		filters.cost_center = get_cost_centers_with_children(filters.cost_center)
		conditions.append("cost_center in %(cost_center)s")

	if filters.get("voucher_no"):
		conditions.append("voucher_no=%(voucher_no)s")

	if not (
		filters.get("account")
		or filters.get("party")
		or filters.get("group_by") in ["Group by Account", "Group by Party"]
	):		
		conditions.append("posting_date >=%(from_date)s")

	conditions.append("(posting_date <=%(to_date)s or is_opening = 'Yes')")

	if filters.get("project"):
		conditions.append("project in %(project)s")

	if filters.get("finance_book"):
		if filters.get("include_default_book_entries"):
			conditions.append(
				"(finance_book in (%(finance_book)s, %(company_fb)s, '') OR finance_book IS NULL)"
			)
		else:
			conditions.append("finance_book in (%(finance_book)s)")

	if not filters.get("show_cancelled_entries"):
		conditions.append("is_cancelled = 0")

	from frappe.desk.reportview import build_match_conditions

	match_conditions = build_match_conditions("GL Entry")

	if match_conditions:
		conditions.append(match_conditions)

	if filters.get("include_dimensions"):
		accounting_dimensions = get_accounting_dimensions(as_list=False)

		if accounting_dimensions:
			for dimension in accounting_dimensions:
				if not dimension.disabled:
					if filters.get(dimension.fieldname):
						if frappe.get_cached_value("DocType", dimension.document_type, "is_tree"):
							filters[dimension.fieldname] = get_dimension_with_children(
								dimension.document_type, filters.get(dimension.fieldname)
							)
							conditions.append("{0} in %({0})s".format(dimension.fieldname))
						else:
							conditions.append("{0} in %({0})s".format(dimension.fieldname))

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_conditions(filters):
	conditions = []
	
	if filters.get("account"):
		filters.account = get_accounts_with_children(filters.account)
		conditions.append("account in %(account)s")

	if filters.get("cost_center"):
		filters.cost_center = get_cost_centers_with_children(filters.cost_center)
		conditions.append("cost_center in %(cost_center)s")
	
	if filters.get("voucher_no"):
		conditions.append("voucher_no=%(voucher_no)s")

	if filters.get("group_by") == "Group by Party" and not filters.get("party_type"):
		conditions.append("party_type in ('Customer', 'Supplier')")

	if filters.get("party_type"):
		conditions.append("party_type=%(party_type)s")

	if filters.get("party"):
		conditions.append("party in %(party)s")

	if not (
		filters.get("account")
		or filters.get("party")
		or filters.get("group_by") in ["Group by Account", "Group by Party"]
	):		
		conditions.append("posting_date >=%(from_date)s")

	conditions.append("(posting_date <=%(to_date)s or is_opening = 'Yes')")

	if filters.get("project"):
		conditions.append("project in %(project)s")

	if filters.get("finance_book"):
		if filters.get("include_default_book_entries"):
			conditions.append(
				"(finance_book in (%(finance_book)s, %(company_fb)s, '') OR finance_book IS NULL)"
			)
		else:
			conditions.append("finance_book in (%(finance_book)s)")

	if not filters.get("show_cancelled_entries"):
		conditions.append("is_cancelled = 0")

	from frappe.desk.reportview import build_match_conditions

	match_conditions = build_match_conditions("GL Entry")

	if match_conditions:
		conditions.append(match_conditions)

	if filters.get("include_dimensions"):
		accounting_dimensions = get_accounting_dimensions(as_list=False)

		if accounting_dimensions:
			for dimension in accounting_dimensions:
				if not dimension.disabled:
					if filters.get(dimension.fieldname):
						if frappe.get_cached_value("DocType", dimension.document_type, "is_tree"):
							filters[dimension.fieldname] = get_dimension_with_children(
								dimension.document_type, filters.get(dimension.fieldname)
							)
							conditions.append("{0} in %({0})s".format(dimension.fieldname))
						else:
							conditions.append("{0} in %({0})s".format(dimension.fieldname))

	return "and {}".format(" and ".join(conditions)) if conditions else ""


def get_accounts_with_children(accounts):
	if not isinstance(accounts, list):
		accounts = [d.strip() for d in accounts.strip().split(",") if d]

	all_accounts = []
	for d in accounts:
		if frappe.db.exists("Account", d):
			lft, rgt = frappe.db.get_value("Account", d, ["lft", "rgt"])
			children = frappe.get_all("Account", filters={"lft": [">=", lft], "rgt": ["<=", rgt]})
			all_accounts += [c.name for c in children]
		else:
			frappe.throw(_("Account: {0} does not exist").format(d))

	return list(set(all_accounts))


def get_data_with_opening_closing(filters, account_details, accounting_dimensions, gl_entries):
	data = []

	gle_map = initialize_gle_map(gl_entries, filters)

	totals, entries = get_accountwise_gle(filters, accounting_dimensions, gl_entries, gle_map)

	# Opening for filtered account
	data.append(totals.opening)

	if filters.get("group_by") != "Group by Voucher (Consolidated)":
		for acc, acc_dict in iteritems(gle_map):
			# acc
			if acc_dict.entries:
				# opening
				data.append({})
				if filters.get("group_by") != "Group by Voucher":
					data.append(acc_dict.totals.opening)

				data += acc_dict.entries

				# totals
				data.append(acc_dict.totals.total)

				# closing
				if filters.get("group_by") != "Group by Voucher":
					data.append(acc_dict.totals.closing)
		data.append({})
	else:
		data += entries

	# totals
	data.append(totals.total)

	# closing
	data.append(totals.closing)

	if filters.get('print_with_item'):
		purchase_invoice_map,total_taxes_and_charges = get_sales_purchase_invoice_data(filters)
		
		for d in data:
			try:
				if d.get('name'):
					d['si_details'] = html_sales_invoice_purchase_invoic_data(purchase_invoice_map[d.name],total_taxes_and_charges[d.name])
				else:
					d['si_details'] = ''
			except KeyError:
				d['si_details'] = ''
	return data

def get_sales_purchase_invoice_data(filters):
	conditions = "gle.is_cancelled = 0"
	conditions += f" AND gle.`posting_date` >= '{filters.from_date}'"	
	conditions += f" AND gle.`posting_date` <= '{filters.to_date}'"
	conditions += f" AND gle.`party_type` = '{filters.party_type}'" if filters.get('party_type') else f" AND gle.`party_type` in ('Customer', 'Supplier')"
	conditions += f" AND gle.`party` = {list_to_sql(filters.get('party'))}" if filters.get('party') else ''
	
	pi_data = frappe.db.sql(f"""
		SELECT 
			gle.name, pii.parent as pi_name,pii.item_name,pii.item_code, pi.total,pi.rounded_total, pii.rate, pii.qty
		FROM
			`tabGL Entry` as gle
			JOIN `tabPurchase Invoice Item` as pii ON pii.parent=gle.voucher_no
			JOIN `tabPurchase Invoice` as pi ON pi.name = gle.voucher_no
		WHERE
			{conditions} AND gle.voucher_type = 'Purchase Invoice'
	""", as_dict = True)
	
	pi_data += frappe.db.sql(f"""
		SELECT 
			gle.name, sii.parent as si_name,sii.item_name,sii.item_code, si.total,si.rounded_total, sii.rate, sii.qty
		FROM
			`tabGL Entry` as gle
			JOIN `tabSales Invoice Item` as sii ON sii.parent=gle.voucher_no
			JOIN `tabSales Invoice` as si ON si.name = gle.voucher_no
		WHERE
			{conditions} AND gle.voucher_type = 'Sales Invoice'
	""", as_dict = True)
	
	purchase_invoice_map = {}
	total_taxes_and_charges = {}
	for row in pi_data:
		total_taxes_and_charges[row.name] = row.rounded_total - row.total
		purchase_invoice_map.setdefault(row.name, {})\
		.setdefault(row.item_code, {})\
		.setdefault(row.rate, frappe._dict({
				"qty": 0.0,
				"item_name": ""
		}))
		purchase_invoice__dict = purchase_invoice_map[row.name][row.item_code][row.rate]
		purchase_invoice__dict.qty += row.qty
		purchase_invoice__dict.item_name += row.item_name

	return purchase_invoice_map,total_taxes_and_charges


def get_totals_dict():
	def _get_debit_credit_dict(label):
		return _dict(
			account="'{0}'".format(label),
			debit=0.0,
			credit=0.0,
			debit_in_account_currency=0.0,
			credit_in_account_currency=0.0,
		)

	return _dict(
		opening=_get_debit_credit_dict(TRANSLATIONS.OPENING),
		total=_get_debit_credit_dict(TRANSLATIONS.TOTAL),
		closing=_get_debit_credit_dict(TRANSLATIONS.CLOSING_TOTAL),
	)


def group_by_field(group_by):
	if group_by == "Group by Party":
		return "party"
	elif group_by in ["Group by Voucher (Consolidated)", "Group by Account"]:
		return "account"
	else:
		return "voucher_no"


def initialize_gle_map(gl_entries, filters):
	gle_map = OrderedDict()
	group_by = group_by_field(filters.get("group_by"))

	for gle in gl_entries:
		gle_map.setdefault(gle.get(group_by), _dict(totals=get_totals_dict(), entries=[]))
	return gle_map


def get_accountwise_gle(filters, accounting_dimensions, gl_entries, gle_map):
	totals = get_totals_dict()
	entries = []
	consolidated_gle = OrderedDict()
	group_by = group_by_field(filters.get("group_by"))
	group_by_voucher_consolidated = filters.get("group_by") == "Group by Voucher (Consolidated)"

	if filters.get("show_net_values_in_party_account"):
		account_type_map = get_account_type_map(filters.get("company"))

	def update_value_in_dict(data, key, gle):
		data[key].debit += gle.debit
		data[key].credit += gle.credit

		data[key].debit_in_account_currency += gle.debit_in_account_currency
		data[key].credit_in_account_currency += gle.credit_in_account_currency

		if filters.get("show_net_values_in_party_account") and account_type_map.get(
			data[key].account
		) in ("Receivable", "Payable"):
			net_value = data[key].debit - data[key].credit
			net_value_in_account_currency = (
				data[key].debit_in_account_currency - data[key].credit_in_account_currency
			)

			if net_value < 0:
				dr_or_cr = "credit"
				rev_dr_or_cr = "debit"
			else:
				dr_or_cr = "debit"
				rev_dr_or_cr = "credit"

			data[key][dr_or_cr] = abs(net_value)
			data[key][dr_or_cr + "_in_account_currency"] = abs(net_value_in_account_currency)
			data[key][rev_dr_or_cr] = 0
			data[key][rev_dr_or_cr + "_in_account_currency"] = 0

		if data[key].against_voucher and gle.against_voucher:
			data[key].against_voucher += ", " + gle.against_voucher

	from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)
	show_opening_entries = filters.get("show_opening_entries")

	for gle in gl_entries:
		group_by_value = gle.get(group_by)

		if gle.posting_date < from_date or (cstr(gle.is_opening) == "Yes" and not show_opening_entries):
			if not group_by_voucher_consolidated:
				update_value_in_dict(gle_map[group_by_value].totals, "opening", gle)
				update_value_in_dict(gle_map[group_by_value].totals, "closing", gle)

			update_value_in_dict(totals, "opening", gle)
			update_value_in_dict(totals, "closing", gle)

		elif gle.posting_date <= to_date:
			if not group_by_voucher_consolidated:
				update_value_in_dict(gle_map[group_by_value].totals, "total", gle)
				update_value_in_dict(gle_map[group_by_value].totals, "closing", gle)
				update_value_in_dict(totals, "total", gle)
				update_value_in_dict(totals, "closing", gle)

				gle_map[group_by_value].entries.append(gle)

			elif group_by_voucher_consolidated:
				keylist = [
					gle.get("voucher_type"),
					gle.get("voucher_no"),
					gle.get("account"),
					gle.get("party_type"),
					gle.get("party"),
				]
				if filters.get("include_dimensions"):
					for dim in accounting_dimensions:
						keylist.append(gle.get(dim))
					keylist.append(gle.get("cost_center"))

				key = tuple(keylist)
				if key not in consolidated_gle:
					consolidated_gle.setdefault(key, gle)
				else:
					update_value_in_dict(consolidated_gle, key, gle)

	for key, value in consolidated_gle.items():
		update_value_in_dict(totals, "total", value)
		update_value_in_dict(totals, "closing", value)
		entries.append(value)

	return totals, entries


def get_account_type_map(company):
	account_type_map = frappe._dict(
		frappe.get_all(
			"Account", fields=["name", "account_type"], filters={"company": company}, as_list=1
		)
	)

	return account_type_map


def get_result_as_list(data, filters):
	balance, balance_in_account_currency = 0, 0
	inv_details = get_supplier_invoice_details()

	for d in data:
		if not d.get("posting_date"):
			balance, balance_in_account_currency = 0, 0

		balance = get_balance(d, balance, "debit", "credit")
		d["balance"] = balance

		d["account_currency"] = filters.account_currency
		d["bill_no"] = inv_details.get(d.get("against_voucher"), "")

	return data


def html_sales_invoice_purchase_invoic_data(purchase_invoice_map,total_taxes_and_charges):
	table = ""
	for item_code,value in purchase_invoice_map.items():
			for k,v in value.items():
				table+= f"""
						<p style="font-size:10px">
							<strong>{v["item_name"]}</strong>
						</p>
						<p style="font-size:10px">
							{v["qty"]} x {frappe.format(k,{'fieldtype': 'Currency'})} = <span><strong>{frappe.format(v["qty"] * k,{'fieldtype': 'Currency'})}</strong></span>
						</p>	
					"""
	if total_taxes_and_charges:
		table += f"""<p>
			<span><strong>Taxes & Charges = {frappe.format(total_taxes_and_charges,{'fieldtype': 'Currency'})}</strong></span>
		</p>
	"""
	return table

def list_to_sql(lst):
    return "(" + ", ".join([f'"{l}"' for l in lst]) + ")"


def get_supplier_invoice_details():
	inv_details = {}
	for d in frappe.db.sql(
		""" select name, bill_no from `tabPurchase Invoice`
		where docstatus = 1 and bill_no is not null and bill_no != '' """,
		as_dict=1,
	):
		inv_details[d.name] = d.bill_no

	return inv_details


def get_balance(row, balance, debit_field, credit_field):
	balance += row.get(debit_field, 0) - row.get(credit_field, 0)

	return balance


def get_columns(filters):
	if filters.get("presentation_currency"):
		currency = filters["presentation_currency"]
	else:
		if filters.get("company"):
			currency = get_company_currency(filters["company"])
		else:
			company = get_default_company()
			currency = get_company_currency(company)

	columns = [
		{
			"label": _("GL Entry"),
			"fieldname": "gl_entry",
			"fieldtype": "Link",
			"options": "GL Entry",
			"hidden": 1,
		},
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 90
		},
		{
			"label": _("Account"),
			"fieldname": "account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 180
		},
		{
			"label": _("Debit ({0})".format(currency)),
			"fieldname": "debit",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Credit ({0})".format(currency)),
			"fieldname": "credit",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Balance ({0})".format(currency)),
			"fieldname": "balance",
			"fieldtype": "Float",
			"width": 130
		}
	]

	columns.extend([
		{
			"label": _("Voucher Type"),
			"fieldname": "voucher_type",
			"width": 120
		},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 180
		},
		{
			"label": _("Against Account"),
			"fieldname": "against",
			"width": 120
		},
		{
			"label": _("Party Type"),
			"fieldname": "party_type",
			"width": 100
		},
		{
			"label": _("Party"),
			"fieldname": "party",
			"width": 100
		},
		{
			"label": _("Project"),
			"options": "Project",
			"fieldname": "project",
			"width": 100
		},
		{
			"label": _("Cost Center"),
			"options": "Cost Center",
			"fieldname": "cost_center",
			"width": 100
		},
		{
			"label": _("Against Voucher Type"),
			"fieldname": "against_voucher_type",
			"width": 100
		},
		{
			"label": _("Against Voucher"),
			"fieldname": "against_voucher",
			"fieldtype": "Dynamic Link",
			"options": "against_voucher_type",
			"width": 100
		},
		{
			"label": _("Supplier Invoice No"),
			"fieldname": "bill_no",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Remarks"),
			"fieldname": "remarks",
			"width": 400
		},
		{
			"label": _("debit credit list"),
			"fieldname": "debit_credit_list",
			"width": 400
		}
	])

	return columns