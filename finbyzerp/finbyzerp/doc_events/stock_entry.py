import frappe
from frappe.utils import flt
from frappe.utils import get_link_to_form

def after_insert(self, method):
	create_quality_inspection_entry(self)

def create_quality_inspection_entry(self):
	# TODO: to be done in version-15
	# TODO: need to check if fields exists in custom field export
 
	for row in self.items:
		item = frappe.get_doc("Item", row.item_code)
		if self.purpose in ["Manufacture", "Repack"]:
			if item.inspection_required_after_stock_entry and row.is_finished_item and row.t_warehouse:
				quality_inspection = frappe.new_doc("Quality Inspection")
				quality_inspection.naming_series = 'MAT-IS-.YYYY.-'
				quality_inspection.item_code = row.item_code
				quality_inspection.ref_item = row.name
				quality_inspection.inspection_type = "Outgoing"
				quality_inspection.reference_type = "Stock Entry"
				quality_inspection.reference_name = self.name
				quality_inspection.sample_size = row.qty
				quality_inspection.qty=row.qty
				quality_inspection.description = row.description
				quality_inspection.remarks = self.remarks
				quality_inspection.inspected_by = self.modified_by
				quality_inspection.lot_no = row.lot_no
				quality_inspection.sample_size_uom = row.uom
				quality_inspection.batch_no = row.batch_no
				quality_inspection.quality_inspection_template = frappe.db.get_value("Item", row.item_code, 'quality_inspection_template')
				quality_inspection.save(ignore_permissions=True)
				frappe.db.set_value(row.doctype, row.name, 'quality_inspection', quality_inspection.name)
				
				frappe.msgprint("Quality Inspection {} is Created".format(get_link_to_form('Quality Inspection', quality_inspection.name)))

@frappe.whitelist()
def check_rate_diff(doctype,docname):
	diff_list = []
	doc = frappe.get_doc(doctype,docname)
	for item in doc.items:
		if item.s_warehouse:
			sle_val_diff,actual_qty = frappe.db.get_value("Stock Ledger Entry",{"voucher_type":doc.doctype,"voucher_no":doc.name,"voucher_detail_no":item.name,"actual_qty":("<",0),"is_cancelled":0},["stock_value_difference","actual_qty"])
			sle_valuation_rate = flt(sle_val_diff) / flt(actual_qty)
			if flt(item.valuation_rate,2) != flt(sle_valuation_rate,2):
				diff_list.append(frappe._dict({"idx":item.idx,"item_code":item.item_code,"entry_rate":flt(item.valuation_rate),"ledger_rate":flt(sle_valuation_rate),"rate_diff":flt(item.valuation_rate) - flt(sle_valuation_rate)}))
	table = None
	if diff_list:
		table = """<table class="table table-bordered" style="margin: 0; font-size:90%;">
			<thead>
				<tr>
					<th>Idx</th>
					<th>Item</th>
					<th>Entry Rate</th>
					<th>Ledger Rate</th>
					<th>Rate Diff</th>
				<tr>
			</thead>
		<tbody>"""
		for item in diff_list:
			table += f"""
				<tr>
					<td>{item.idx}</td>
					<td>{item.item_code}</td>
					<td>{item.entry_rate}</td>
					<td>{item.ledger_rate}</td>
					<td>{item.rate_diff}</td>
				</tr>
			"""
		
		table += """
		</tbody></table>
		"""
	return table if table else "Difference Not Found"
		# frappe.msgprint(
		# 	title = "Items Rate Difference",
		# 	msg = str(table),
		# 	wide = True)

def on_submit(self, method):
	for inspection_item in self.items:
		item = frappe.get_doc("Item", inspection_item.item_code)
		if item.inspection_required_after_stock_entry:
			doc = frappe.db.exists("Quality Inspection",{'reference_name':self.name,'docstatus': 0})
			if doc:
				qi_doc = frappe.get_doc("Quality Inspection",doc)
				if qi_doc.docstatus == 0:
					frappe.throw("Quality Inspection Is Not Submited <br> Please Submit Quality Inspection {}".format(get_link_to_form("Quality Inspection",doc)))