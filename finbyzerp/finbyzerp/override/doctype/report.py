import frappe
from frappe import _
from frappe.core.doctype.report.report import Report


class CustomReport(Report):
    def validate(self):
        """only administrator can save standard report"""
        
        if not self.module:
            self.module = frappe.db.get_value("DocType", self.ref_doctype, "module")

        if not self.is_standard:
            self.is_standard = "No"
            if frappe.session.user=="Administrator" and getattr(frappe.local.conf, 'developer_mode',0)==1:
                self.is_standard = "Yes"

        if self.is_standard == "No":
            # allow only script manager to edit scripts
            if self.report_type != 'Report Builder':
                frappe.only_for('Script Manager', True)

            if frappe.db.get_value("Report", self.name, "is_standard") == "Yes":
                frappe.throw(_("Cannot edit a standard report. Please duplicate and create a new report"))

        # finbyz Change in if condition
        if self.is_standard == "Yes" and "Local Admin" not in frappe.get_roles(frappe.session.user):
            frappe.throw(_("Only Administrator can save a standard report. Please rename and save."))

        if self.report_type == "Report Builder":
            self.update_report_json()