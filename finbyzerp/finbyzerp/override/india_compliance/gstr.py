import frappe

def get_transaction(self, category, supplier, invoice):
    invoice['items'] = [{
        "num": 1,
        "sgst": invoice.get("sgst", 0),
        "cgst": invoice.get("cgst", 0),
        "igst": invoice.get("igst", 0),
        "cess": invoice.get("cess", 0),
        "txval": invoice.get("txval", 0)
    }]
    transaction = frappe._dict(
        company=self.company,
        company_gstin=self.gstin,
        classification=category.value,
        **self.get_supplier_details(supplier),
        **self.get_invoice_details(invoice),
        items=self.get_transaction_items(invoice),
    )

    transaction["unique_key"] = (
        f"{transaction.get('supplier_gstin', '')}-{transaction.get('bill_no', '')}"
    )

    return transaction