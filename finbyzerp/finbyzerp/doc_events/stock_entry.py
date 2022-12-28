import frappe
from frappe.utils import flt
from erpnext.stock.doctype.item.item import get_item_defaults

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
	
from frappe.utils import cint, comma_or, cstr, flt, format_time, formatdate, getdate, nowdate
from six import iteritems, itervalues, string_types
from erpnext.manufacturing.doctype.bom.bom import add_additional_cost, validate_bom_no
import json

@frappe.whitelist()
def qty_as_per_bom(doc, bom, qty, company):
	doc = json.loads(doc)
	from erpnext.manufacturing.doctype.bom.bom import get_bom_items
	item_dict = get_bom_items(bom, company, qty, fetch_exploded=1)
	if doc.get('work_order'):
		item_code = frappe.db.get_value("Work Order", doc['work_order'], "production_item")
		to_warehouse = frappe.db.get_value("Work Order", doc['work_order'], "fg_warehouse")
	else:
		item_code = frappe.db.get_value("BOM", doc.get('bom_no'), "item")
		to_warehouse = doc.get('to_warehouse')

	item = get_item_defaults(item_code, company)

	if not doc.get('work_order') and not to_warehouse:
		# in case of BOM
		to_warehouse = item.get("default_warehouse")

	args = [{
		"item_code":item_code,
		"to_warehouse": to_warehouse,
		"from_warehouse": "",
		"qty": doc.get('fg_completed_qty'),
		"item_name": item.item_name,
		"item_group": item.item_group,
		"description": item.description,
		"stock_uom": item.stock_uom,
		"expense_account": item.get("expense_account"),
		"cost_center": item.get("buying_cost_center"),
		"is_finished_item": 1
	}]

	return item_dict + args
