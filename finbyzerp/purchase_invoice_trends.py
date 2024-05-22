import frappe
from frappe import _
from erpnext.controllers.trends import get_columns, get_data


def purchase_invoice_trends_execute(filters=None):
	if not filters:
		filters = {}
	data = []
	conditions = get_columns(filters, "Purchase Invoice")
	data = get_data(filters, conditions)
	chart_data = get_chart_data(data, conditions, filters)
	return conditions["columns"], data, None, chart_data

def get_chart_data(data, conditions, filters):
	if not data:
		return []

	labels, datapoints = [], []

	if filters.get("group_by"):
		# consider only consolidated row
		data = [row for row in data if row[0]]

	data = sorted(data, key=lambda i: i[-1], reverse=True)

	if len(data) > 10:
		# get top 10 if data too long
		data = data[:10]

	for row in data:
		labels.append(row[0])
		datapoints.append(row[-1])

	return {
		"data": {
			"labels": labels,
			"datasets": [{"name": _("Total Invoice Amount"), "values": datapoints}],
		},
		"type": "bar",
		"fieldtype": "Currency",
	}

def get_data(filters, conditions):
	data = []
	inc, cond= '',''

	query_details =  conditions["based_on_select"] + conditions["period_wise_select"]

	posting_date = 't1.transaction_date'
	if conditions.get('trans') in ['Sales Invoice', 'Purchase Invoice', 'Purchase Receipt', 'Delivery Note']:
		posting_date = 't1.posting_date'
		if filters.period_based_on:
			posting_date = 't1.'+filters.period_based_on

	if conditions["based_on_select"] in ["t1.project,", "t2.project,"]:
		cond = ' and '+ conditions["based_on_select"][:-1] +' IS Not NULL'
	if conditions.get('trans') in ['Sales Order', 'Purchase Order']:
		cond += " and t1.status != 'Closed'"

	if conditions.get('trans') == 'Quotation' and filters.get("group_by") == 'Customer':
		cond += " and t1.quotation_to = 'Customer'"

	year_start_date, year_end_date = frappe.get_cached_value(
		"Fiscal Year", filters.get("fiscal_year"), ["year_start_date", "year_end_date"]
	)

	parent_condition = ''
	if filters.get('item'):
		parent_condition += f"and t2.item_code = {frappe.db.escape(filters.get('item'))}"
	
	elif filters.get('supplier'):
		parent_condition += f"and t1.supplier = {frappe.db.escape(filters.get('supplier'))}"

	elif filters.get('supplier_group'):
		parent_condition += f"and t1.supplier_group = {frappe.db.escape(filters.get('supplier_group'))}"


	elif filters.get('item_group'):
		parent_condition += f"and t2.item_group = {frappe.db.escape(filters.get('item_group'))}"

	elif filters.get('cost_center'):
		parent_condition += f"and t2.cost_center = '{filters.get('cost_center')}'"

	if filters.get("group_by"):
		sel_col = ''
		item_name = ''
		ind = conditions["columns"].index(conditions["grbc"][0])
		if filters.get("group_by") == 'Item':
			sel_col = 't2.item_code'
			item_name = ', t2.item_name'
		elif filters.get("group_by") == 'Customer':
			sel_col = 't1.party_name' if conditions.get('trans') == 'Quotation' else 't1.customer'
		elif filters.get("group_by") == 'Supplier':
			sel_col = 't1.supplier'
		elif filters.get("group_by") == 'Item Group':
			sel_col = 't2.item_group'

		if filters.get('based_on') in ['Item','Customer','Supplier']:
			inc = 2
		else :
			inc = 1
		if filters.get('period'):
			query_details.replace('t2.item_name, ', 't2.item_name, ')
		else:
			query_details.replace('t2.item_name, ', 'Null, ')

		data1 = frappe.db.sql(""" select %s from `tab%s` t1, `tab%s Item` t2 %s
					where t2.parent = t1.name and t1.company = %s and %s between %s and %s and
					t1.docstatus = 1 %s %s %s
					group by %s
				""" % (query_details, conditions["trans"],  conditions["trans"], conditions["addl_tables"], "%s",
					posting_date, "%s", "%s", conditions.get("addl_tables_relational_cond"), cond, parent_condition, conditions["group_by"]), (filters.get("company"),
					year_start_date, year_end_date),as_list=1)

		for d in range(len(data1)):
			#to add blanck column
			dt = data1[d]
			dt.insert(ind,'')
			data.append(dt)
			#to get distinct value of col specified by group_by in filter
			row = frappe.db.sql("""select DISTINCT(%s) from `tab%s` t1, `tab%s Item` t2 %s
						where t2.parent = t1.name and t1.company = %s and %s between %s and %s
						and t1.docstatus = 1 and %s = %s %s %s
					""" %
					(sel_col, conditions["trans"],  conditions["trans"], conditions["addl_tables"],
						"%s", posting_date, "%s", "%s", conditions["group_by"], "%s", conditions.get("addl_tables_relational_cond"), cond),
					(filters.get("company"), year_start_date, year_end_date, data1[d][0]), as_list=1)

			for i in range(len(row)):
				des = ['' for q in range(len(conditions["columns"]))]

				#get data for group_by filter
				row1 = frappe.db.sql(""" select %s , %s from `tab%s` t1, `tab%s Item` t2 %s
							where t2.parent = t1.name and t1.company = %s and %s between %s and %s
							and t1.docstatus = 1 and %s = %s and %s = %s %s %s
						""" %
						(sel_col, conditions["period_wise_select"], conditions["trans"],
							conditions["trans"], conditions["addl_tables"], "%s", posting_date, "%s","%s", sel_col,
							"%s", conditions["group_by"], "%s", conditions.get("addl_tables_relational_cond"), cond),
						(filters.get("company"), year_start_date, year_end_date, row[i][0],
							data1[d][0]), as_list=1)
				des[ind] = row[i][0]
				for j in range(1,len(conditions["columns"])-inc):
					des[j+inc] = row1[0][j]

				data.append(des)
	else:
		data = frappe.db.sql(""" select %s from `tab%s` t1, `tab%s Item` t2 %s
					where t2.parent = t1.name and t1.company = %s and %s between %s and %s and
					t1.docstatus = 1 %s %s %s
					group by %s
				""" %
				(query_details, conditions["trans"], conditions["trans"], conditions["addl_tables"],
					"%s", posting_date, "%s", "%s", cond, conditions.get("addl_tables_relational_cond", ""), parent_condition, conditions["group_by"]),
				(filters.get("company"), year_start_date, year_end_date), as_list=1)

	return data