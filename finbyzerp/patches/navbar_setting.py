from __future__ import unicode_literals
import frappe


def execute():
    update_help_drop_down()

def update_help_drop_down():   
    doc = frappe.get_doc("Navbar Settings")
    for row in doc.help_dropdown:
        if row.item_label == "Report an Issue":
            row.item_label = "Youtube Tutorials"
            row.item_type = "Route"
            row.route = "https://www.youtube.com/@Finbyz"
            break
    doc.save()