import frappe


def on_submit(self, method):
    set_batch_in_quality_inspection(self)


def set_batch_in_quality_inspection(self):
    for row in self.items:
        if row.batch_no and row.quality_inspection:
            doc = frappe.get_doc("Quality Inspection", row.quality_inspection)
            doc.db_set("batch_no", row.batch_no)
