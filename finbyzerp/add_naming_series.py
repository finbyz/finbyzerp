import frappe


def create_property_setter(doc_type, series):
    if frappe.db.exists("Property Setter", f"{doc_type}-naming_series-options"):
        frappe.delete_doc("Property Setter", f"{doc_type}-naming_series-options")
    
    if frappe.db.exists("Property Setter", f"{doc_type}-naming_series-default"):
        frappe.delete_doc("Property Setter", f"{doc_type}-naming_series-default")
    
    doc = frappe.new_doc("Property Setter")
    doc.doctype_or_field = "DocField"
    doc.doc_type = doc_type
    doc.field_name = "naming_series"
    doc.property = "options"
    doc.property_type = "Text"
    doc.value = series
    doc.flags.ignore_permissions = True
    doc.save()

    doc = frappe.new_doc("Property Setter")
    doc.doctype_or_field = "DocField"
    doc.doc_type = doc_type
    doc.field_name = "naming_series"
    doc.property = "default"
    doc.property_type = "Text"
    doc.value = series
    doc.flags.ignore_permissions = True
    doc.save()



def add_naming_series():
    data = [
        {"doc_type": "Pick List", "series": "PICK.company_series.-.fiscal."},
        {"doc_type": "Sales Invoice", "series": "SINV.company_series.-.fiscal."},
        {"doc_type": "Purchase Invoice", "series": "PINV.company_series.-.fiscal."},
        {"doc_type": "Payment Request", "series": "PRQ.company_series.-.fiscal."},
        {"doc_type": "Payment Entry", "series": "PAY.company_series.-.fiscal."},
        {"doc_type": "Journal Entry", "series": "JV.company_series.-.fiscal."},
        {"doc_type": "Material Request", "series": "MR.company_series.-.fiscal."},
        {"doc_type": "Purchase Order", "series": "PUR.company_series.-.fiscal."},
        {"doc_type": "Work Order", "series": "WO.company_series.-.fiscal."},
        {"doc_type": "Purchase Order", "series": "PUR.company_series.-.fiscal."},
        {"doc_type": "Production Plan", "series": "PP.company_series.-.fiscal."},
        {"doc_type": "Purchase Order", "series": "PUR.company_series.-.fiscal."},
        {"doc_type": "Stock Entry", "series": "STE.company_series.-.fiscal."},
        {"doc_type": "Purchase Order", "series": "PUR.company_series.-.fiscal."},
        {"doc_type": "Quotation", "series": "QTN.company_series.-.fiscal."},
        {"doc_type": "Sales Order", "series": "ORD.company_series.-.fiscal."},
        {"doc_type": "Delivery Note", "series": "DN.company_series.-.fiscal."},
        {"doc_type": "Purchase Receipt", "series": "PRE.company_series.-.fiscal."},
        {"doc_type": "Packing Slip", "series": "PAC.company_series.-.fiscal."},
        {"doc_type": "Asset", "series": "ASS.company_series.-.fiscal."},
    ]

    for row in data:
        create_property_setter(**row)
