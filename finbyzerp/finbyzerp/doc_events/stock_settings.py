import frappe
from erpnext.stock.doctype.stock_settings.stock_settings import StockSettings


def validate(self, method):
    create_property_setter(self)


def create_property_setter(self: StockSettings):
    property_setter = [
        {
            "doctype_or_field": "DocField",
            "doc_type": "Purchase Order Item",
            "field_name": "stock_qty",
            "property": "read_only",
            "property_type": "Check",
            "value": "0",
        },
        {
            "doctype_or_field": "DocField",
            "doc_type": "Purchase Order Item",
            "field_name": "conversion_factor",
            "property": "read_only",
            "property_type": "Check",
            "value": "1",
        },
        {
            "doctype_or_field": "DocField",
            "doc_type": "Purchase Receipt Item",
            "field_name": "stock_qty",
            "property": "read_only",
            "property_type": "Check",
            "value": "0",
        },
        {
            "doctype_or_field": "DocField",
            "doc_type": "Purchase Receipt Item",
            "field_name": "conversion_factor",
            "property": "read_only",
            "property_type": "Check",
            "value": "1",
        },
        {
            "doctype_or_field": "DocField",
            "doc_type": "Purchase Invoice Item",
            "field_name": "stock_qty",
            "property": "read_only",
            "property_type": "Check",
            "value": "0",
        },
        {
            "doctype_or_field": "DocField",
            "doc_type": "Purchase Invoice Item",
            "field_name": "conversion_factor",
            "property": "read_only",
            "property_type": "Check",
            "value": "1",
        },
    ]

    if self.calculate_conversion_factor_based_on_stock_quantity_and_quantity:
        for row in property_setter:
            property_setter_name =  f'{row["doc_type"]}-{row["field_name"]}-{row["property"]}'
            if not frappe.db.exists("Property Setter", property_setter_name):
                doc = frappe.new_doc("Property Setter")
                doc.update(row)
                doc.save(ignore_permissions=True)
    else:
        for row in property_setter:
            property_setter_name =  f'{row["doc_type"]}-{row["field_name"]}-{row["property"]}'
            if frappe.db.exists("Property Setter", property_setter_name):
                doc = frappe.get_doc("Property Setter", property_setter_name)
                doc.delete()
