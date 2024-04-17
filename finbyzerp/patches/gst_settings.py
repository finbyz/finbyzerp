from __future__ import unicode_literals
import frappe


def execute():
    update_use_update_party_information()

def update_use_update_party_information():
    frappe.db.set_value("GST Settings",None,'archive_party_info_days',120,update_modified=True)
    frappe.db.commit()