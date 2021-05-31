from __future__ import unicode_literals
from frappe import _

def get_data(data):
	return {
		'fieldname': 'opportunity',
		'transactions': [
			{
				'items': ['Quotation', 'Supplier Quotation','Meeting Schedule','Meeting']
			},
		]
	}