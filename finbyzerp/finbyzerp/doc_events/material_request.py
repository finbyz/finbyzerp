import frappe

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_default_supplier_query(doctype, txt, searchfield, start, page_len, filters):

	doc = frappe.get_doc("Material Request", filters.get("doc"))
	item_list = []
	for d in doc.items:
		item_list.append(d.item_code)

	supplier_data = frappe.db.sql("""select default_supplier
		from `tabItem Default`
		where parent in ({0}) and
		default_supplier IS NOT NULL
		""".format(', '.join(['%s']*len(item_list))),tuple(item_list))
	

	supplier_data += frappe.db.sql("""select supplier
		from `tabItem Supplier`
		where parent in ({0}) and
		supplier IS NOT NULL
		""".format(', '.join(['%s']*len(item_list))),tuple(item_list))
	
	return supplier_data