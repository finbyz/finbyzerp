import frappe
from frappe.utils import flt
def validate(self,method):
	validate_s_and_t_warehoouse(self)
	
def validate_s_and_t_warehoouse(self):
	if self.purpose in ["Material Transfer","Material Transfer for Manufacture"]:
		for row in self.items:
			if row.s_warehouse == row.t_warehouse:
				pass
				#frappe.throw("Source and Target warehouse can not be same for materil transfer entry.")

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