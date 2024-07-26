import frappe
def create_property_setter(self,method):
    property_setter=[
    {'doctype_or_field': 'DocField',
    'doc_type': 'Purchase Order Item',
    'field_name': 'stock_qty',
    'property': 'read_only',
    'property_type': 'Check',
    'value': '0',
    },
    {'doctype_or_field': 'DocField',
    'doc_type': 'Purchase Order Item',
    'field_name': 'conversion_factor',
    'property': 'read_only',
    'property_type': 'Check',
    'value': '1',
    },
    {'doctype_or_field': 'DocField',
    'doc_type': 'Purchase Receipt Item',
    'field_name': 'stock_qty',
    'property': 'read_only',
    'property_type': 'Check',
    'value': '0',
    },
    {'doctype_or_field': 'DocField',
    'doc_type': 'Purchase Receipt Item',
    'field_name': 'conversion_factor',
    'property': 'read_only',
    'property_type': 'Check',
    'value': '1',
    },
    {'doctype_or_field': 'DocField',
    'doc_type': 'Purchase Invoice Item',
    'field_name': 'stock_qty',
    'property': 'read_only',
    'property_type': 'Check',
    'value': '0',
    },
    {'doctype_or_field': 'DocField',
    'doc_type': 'Purchase Invoice Item',
    'field_name': 'conversion_factor',
    'property': 'read_only',
    'property_type': 'Check',
    'value': '1',
    }]
    if self.calculate_conversion_factor_based_on_stock_quantity_and_quantity:
        for each in property_setter:
            name = str(each.get('doc_type')) + '-' + str(each.get('field_name')) + '-' + str(each.get('property'))
            if not frappe.db.exists("Property Setter", name):
                doc = frappe.new_doc("Property Setter")
                doc.update(each)
                doc.save(ignore_permissions=True)
    else:
        for each in property_setter:
            name = str(each.get('doc_type')) + '-' + str(each.get('field_name')) + '-' + str(each.get('property'))
            if frappe.db.exists("Property Setter", name):
                doc = frappe.get_doc("Property Setter", name)
                doc.delete()

