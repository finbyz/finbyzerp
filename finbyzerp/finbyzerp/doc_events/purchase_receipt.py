import frappe
<<<<<<< HEAD
def validate(self, method):
    conversion_factor = frappe.db.get_single_value("Stock Settings", "calculate_conversion_factor_based_on_stock_quantity_and_quantity")
    if conversion_factor:
        for i in self.items:
            if(i.qty>0):
                i.conversion_factor = (i.stock_qty/i.qty)
=======

def set_batch_in_qc(self, method):
	for row in self.items:
		if row.batch_no and row.quality_inspection:
			doc = frappe.get_doc("Quality Inspection", row.quality_inspection)
			doc.db_set("batch_no", row.batch_no)
>>>>>>> b9f4bb7ff923061248276574124a8461d74eab15
