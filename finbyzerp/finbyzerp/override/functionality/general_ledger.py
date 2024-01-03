from erpnext.accounts.report.general_ledger.general_ledger import get_balance, get_supplier_invoice_details


def get_result_as_list(data, filters):
    balance, balance_in_account_currency = 0, 0
    inv_details = get_supplier_invoice_details()
    map_bill_no = {}
    for d in data:
        if not d.get("posting_date"):
            balance, balance_in_account_currency = 0, 0

        balance = get_balance(d, balance, "debit", "credit")
        d["balance"] = balance

        d["account_currency"] = filters.account_currency
        d["bill_no"] = inv_details.get(d.get("against_voucher"), "")
        if d.get("bill_no"):
            map_bill_no[d.get("voucher_no")] = inv_details.get(d.get("against_voucher"), "")

    for row in data:
        if not row.get("bill_no"):
            row["bill_no"] = map_bill_no.get(row.get("voucher_no"))

    return data
