# Copyright (c) 2021, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

# import frappe
from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class BankStatementSettings(Document):
	def autoname(self):
		self.name = self.bank + "-Statement-Settings"