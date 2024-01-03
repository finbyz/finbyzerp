import frappe
from frappe import _
from frappe.utils import flt
from erpnext.controllers.sales_and_purchase_return import get_ref_item_dict, get_already_returned_items, validate_quantity

def validate_returned_items(doc):
	from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos

	valid_items = frappe._dict()

	select_fields = "item_code, qty, stock_qty, rate, parenttype, conversion_factor"
	if doc.doctype != "Purchase Invoice":
		select_fields += ",serial_no, batch_no"

	if doc.doctype in ["Purchase Invoice", "Purchase Receipt"]:
		select_fields += ",rejected_qty, received_qty"

	for d in frappe.db.sql(
		"""select {0} from `tab{1} Item` where parent = %s""".format(select_fields, doc.doctype),
		doc.return_against,
		as_dict=1,
	):
		valid_items = get_ref_item_dict(valid_items, d)

	if doc.doctype in ("Delivery Note", "Sales Invoice"):
		for d in frappe.db.sql(
			"""select item_code, qty, serial_no, batch_no from `tabPacked Item`
			where parent = %s""",
			doc.return_against,
			as_dict=1,
		):
			valid_items = get_ref_item_dict(valid_items, d)

	already_returned_items = get_already_returned_items(doc)

	# ( not mandatory when it is Purchase Invoice or a Sales Invoice without Update Stock )
	warehouse_mandatory = not (
		(doc.doctype == "Purchase Invoice" or doc.doctype == "Sales Invoice") and not doc.update_stock
	)

	items_returned = False
	for d in doc.get("items"):
		if d.item_code and (flt(d.qty) < 0 or flt(d.get("received_qty")) < 0):
			if d.item_code not in valid_items:
				#finbyz chnages start
				pass
				# frappe.throw(
				# 	_("Row # {0}: Returned Item {1} does not exist in {2} {3}").format(
				# 		d.idx, d.item_code, doc.doctype, doc.return_against
				# 	)
				# )
				#finbyz chnages start
			else:
				ref = valid_items.get(d.item_code, frappe._dict())
				validate_quantity(doc, d, ref, valid_items, already_returned_items)

				if ref.rate and doc.doctype in ("Delivery Note", "Sales Invoice") and flt(d.rate) > ref.rate:
					frappe.throw(
						_("Row # {0}: Rate cannot be greater than the rate used in {1} {2}").format(
							d.idx, doc.doctype, doc.return_against
						)
					)

				elif ref.batch_no and d.batch_no not in ref.batch_no:
					frappe.throw(
						_("Row # {0}: Batch No must be same as {1} {2}").format(
							d.idx, doc.doctype, doc.return_against
						)
					)

				elif ref.serial_no:
					if not d.serial_no:
						frappe.throw(_("Row # {0}: Serial No is mandatory").format(d.idx))
					else:
						serial_nos = get_serial_nos(d.serial_no)
						for s in serial_nos:
							if s not in ref.serial_no:
								frappe.throw(
									_("Row # {0}: Serial No {1} does not match with {2} {3}").format(
										d.idx, s, doc.doctype, doc.return_against
									)
								)

				if (
					warehouse_mandatory
					and not d.get("warehouse")
					and frappe.db.get_value("Item", d.item_code, "is_stock_item")
				):
					frappe.throw(_("Warehouse is mandatory"))

			items_returned = True

		elif d.item_name:
			items_returned = True

	if not items_returned:
		frappe.throw(_("Atleast one item should be entered with negative quantity in return document"))
