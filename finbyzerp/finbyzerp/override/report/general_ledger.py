from erpnext.accounts.report.general_ledger.general_ledger import get_result,update_translations,validate_filters ,validate_party,set_account_currency,get_columns
import frappe


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

	if filters.get("account"):
		for row in res:
			if row.get('voucher_no'):
				meta = frappe.get_meta(row.voucher_type)
				if meta.has_field('bill_no'):
					row.update({'bill_no':frappe.db.get_value(row.voucher_type , row.voucher_no , 'bill_no')})
				

	return columns, res