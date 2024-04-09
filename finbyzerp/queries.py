import frappe
from frappe.desk.reportview import get_filters_cond, get_match_cond
from erpnext.controllers.queries import get_fields

# searches for supplier
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def supplier_query(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
	doctype = "Supplier"
	supp_master_name = frappe.defaults.get_user_default("supp_master_name")
	fields = ["name"]
	if supp_master_name != "Supplier Name":
		fields.append("supplier_name")

	fields = get_fields(doctype, fields)
	searchfields = frappe.get_meta(doctype).get_search_fields()
	searchfields = " or ".join(field + " like %(txt)s" for field in searchfields)
	return frappe.db.sql(
		"""select {field} from `tabSupplier`
		where docstatus < 2
			and ({searchfields}
			or supplier_name like %(txt)s) and disabled=0
			and (on_hold = 0 or (on_hold = 1 and CURRENT_DATE > release_date))
			{mcond}
		order by
			(case when locate(%(_txt)s, name) > 0 then locate(%(_txt)s, name) else 99999 end),
			(case when locate(%(_txt)s, supplier_name) > 0 then locate(%(_txt)s, supplier_name) else 99999 end),
			idx desc,
			name, supplier_name
		limit %(page_len)s offset %(start)s""".format(
			**{"field": ", ".join(fields), "searchfields": searchfields, "mcond": get_match_cond(doctype)}
		),
		{"txt": "%%%s%%" % txt, "_txt": txt.replace("%", ""), "start": start, "page_len": page_len},
		as_dict=as_dict,
	)