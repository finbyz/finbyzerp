# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.utils import getdate

from erpnext.controllers.trends import validate_filters, period_wise_columns_query, group_wise_column


def get_columns(filters, trans):
	validate_filters(filters)

	# get conditions for based_on filter cond
	based_on_details = based_wise_columns_query(filters.get("based_on"), trans)
	# get conditions for periodic filter cond
	period_cols, period_select = period_wise_columns_query(filters, trans)
	# get conditions for grouping filter cond
	group_by_cols = group_wise_column(filters.get("group_by"))

	columns = (
		based_on_details["based_on_cols"]
		+ period_cols
		+ [_("Total(Qty)") + ":Float:120", _("Total(Amt)") + ":Currency:120"]
	)
	if group_by_cols:
		columns = (
			based_on_details["based_on_cols"]
			+ group_by_cols
			+ period_cols
			+ [_("Total(Qty)") + ":Float:120", _("Total(Amt)") + ":Currency:120"]
		)

	conditions = {
		"based_on_select": based_on_details["based_on_select"],
		"period_wise_select": period_select,
		"columns": columns,
		"group_by": based_on_details["based_on_group_by"],
		"grbc": group_by_cols,
		"trans": trans,
		"addl_tables": based_on_details["addl_tables"],
		"addl_tables_relational_cond": based_on_details.get("addl_tables_relational_cond", ""),
	}

	return conditions


def get_data(filters, conditions):
	data = []
	inc, cond = "", ""
	query_details = conditions["based_on_select"] + conditions["period_wise_select"]

	posting_date = "t1.transaction_date"
	if conditions.get("trans") in [
		"Sales Invoice",
		"Purchase Invoice",
		"Purchase Receipt",
		"Delivery Note",
	]:
		posting_date = "t1.posting_date"
		if filters.period_based_on:
			posting_date = "t1." + filters.period_based_on

	if conditions["based_on_select"] in ["t1.project,", "t2.project,"]:
		cond = " and " + conditions["based_on_select"][:-1] + " IS Not NULL"
	if conditions.get("trans") in ["Sales Order", "Purchase Order"]:
		cond += " and t1.status != 'Closed'"

	if conditions.get("trans") == "Quotation" and filters.get("group_by") == "Customer":
		cond += " and t1.quotation_to = 'Customer'"

	year_start_date, year_end_date = frappe.get_cached_value(
		"Fiscal Year", filters.get("fiscal_year"), ["year_start_date", "year_end_date"]
	)
	parent_condition = ''
	
	if filters.get("based_on") == "Item" and filters.get('item'):
		parent_condition += f" and t2.item_code = {frappe.db.escape(filters.get('item'))}"
	
	elif filters.get("based_on") == "Customer" and filters.get('customer'):
		parent_condition += f" and t1.customer = {frappe.db.escape(filters.get('customer'))}"

	elif filters.get("based_on") == "Customer Group" and filters.get('customer_group'):
		parent_condition += f" and t1.customer_group = {frappe.db.escape(filters.get('customer_group'))}"

	elif filters.get("based_on") == "Item Group" and filters.get('item_group'):
		parent_condition += f" and t2.item_group = {frappe.db.escape(filters.get('item_group'))}"

	elif filters.get("based_on") == "Cost Center" and filters.get('cost_center'):
		parent_condition += f" and t2.cost_center = '{filters.get('cost_center')}'"
	
	if filters.get("group_by"):
		sel_col = ""
		ind = conditions["columns"].index(conditions["grbc"][0])

		if filters.get("group_by") == "Item":
			sel_col = "t2.item_code"
		if filters.get("group_by") == "Item Group":
			sel_col = "t2.item_group"
		elif filters.get("group_by") == "Customer":
			sel_col = "t1.party_name" if conditions.get("trans") == "Quotation" else "t1.customer"
		elif filters.get("group_by") == "Supplier":
			sel_col = "t1.supplier"
		

		if filters.get("based_on") in ["Item", "Customer", "Supplier"]:
			inc = 2
		else:
			inc = 1
		data1 = frappe.db.sql(
			""" select %s from `tab%s` t1, `tab%s Item` t2 %s
					where t2.parent = t1.name and t1.company = %s and %s between %s and %s and
					t1.docstatus = 1 %s %s %s
					group by %s
				"""
			% (
				query_details,
				conditions["trans"],
				conditions["trans"],
				conditions["addl_tables"],
				"%s",
				posting_date,
				"%s",
				"%s",
				conditions.get("addl_tables_relational_cond"),
				cond,
				parent_condition,
				conditions["group_by"],
			),
			(filters.get("company"), year_start_date, year_end_date),
			as_list=1,
		)

		for d in range(len(data1)):
			# to add blanck column
			dt = data1[d]
			dt.insert(ind, "")
			data.append(dt)

			# to get distinct value of col specified by group_by in filter
			row = frappe.db.sql(
				"""select DISTINCT(%s) from `tab%s` t1, `tab%s Item` t2 %s
						where t2.parent = t1.name and t1.company = %s and %s between %s and %s
						and t1.docstatus = 1 and %s = %s %s %s %s
					"""
				% (
					sel_col,
					conditions["trans"],
					conditions["trans"],
					conditions["addl_tables"],
					"%s",
					posting_date,
					"%s",
					"%s",
					conditions["group_by"],
					"%s",
					conditions.get("addl_tables_relational_cond"),
					cond,
					parent_condition
				),
				(filters.get("company"), year_start_date, year_end_date, data1[d][0]),
				as_list=1,
			)

			for i in range(len(row)):
				des = ["" for q in range(len(conditions["columns"]))]

				# get data for group_by filter
				row1 = frappe.db.sql(
					""" select %s , %s from `tab%s` t1, `tab%s Item` t2 %s
							where t2.parent = t1.name and t1.company = %s and %s between %s and %s
							and t1.docstatus = 1 and %s = %s and %s = %s %s %s %s
						"""
					% (
						sel_col,
						conditions["period_wise_select"],
						conditions["trans"],
						conditions["trans"],
						conditions["addl_tables"],
						"%s",
						posting_date,
						"%s",
						"%s",
						sel_col,
						"%s",
						conditions["group_by"],
						"%s",
						conditions.get("addl_tables_relational_cond"),
						cond,
						parent_condition
					),
					(filters.get("company"), year_start_date, year_end_date, row[i][0], data1[d][0]),
					as_list=1,
				)

				des[ind] = row[i][0]

				for j in range(1, len(conditions["columns"]) - inc):
					des[j + inc] = row1[0][j]

				data.append(des)
	else:
		data = frappe.db.sql(
			""" select %s from `tab%s` t1, `tab%s Item` t2 %s
					where t2.parent = t1.name and t1.company = %s and %s between %s and %s and
					t1.docstatus = 1 %s %s %s
					group by %s
				"""
			% (
				query_details,
				conditions["trans"],
				conditions["trans"],
				conditions["addl_tables"],
				"%s",
				posting_date,
				"%s",
				"%s",
				cond,
				parent_condition,
				conditions.get("addl_tables_relational_cond", ""),
				conditions["group_by"],
			),
			(filters.get("company"), year_start_date, year_end_date),
			as_list=1,
		)

	return data


def based_wise_columns_query(based_on, trans):
	based_on_details = {}

	# based_on_cols, based_on_select, based_on_group_by, addl_tables
	if based_on == "Item":
		based_on_details["based_on_cols"] = ["Item:Link/Item:120", "Item Name:Data:120"]
		based_on_details["based_on_select"] = "t2.item_code, t2.item_name,"
		based_on_details["based_on_group_by"] = "t2.item_code"
		based_on_details["addl_tables"] = ""

	elif based_on == "Item Group":
		based_on_details["based_on_cols"] = ["Item Group:Link/Item Group:120"]
		based_on_details["based_on_select"] = "t2.item_group,"
		based_on_details["based_on_group_by"] = "t2.item_group"
		based_on_details["addl_tables"] = ""

	elif based_on == "Customer":
		based_on_details["based_on_cols"] = [
			"Customer:Link/Customer:120",
			"Territory:Link/Territory:120",
		]
		based_on_details["based_on_select"] = "t1.customer_name, t1.territory, "
		based_on_details["based_on_group_by"] = (
			"t1.party_name" if trans == "Quotation" else "t1.customer"
		)
		based_on_details["addl_tables"] = ""

	elif based_on == "Customer Group":
		based_on_details["based_on_cols"] = ["Customer Group:Link/Customer Group"]
		based_on_details["based_on_select"] = "t1.customer_group,"
		based_on_details["based_on_group_by"] = "t1.customer_group"
		based_on_details["addl_tables"] = ""

	elif based_on == "Supplier":
		based_on_details["based_on_cols"] = [
			"Supplier:Link/Supplier:120",
			"Supplier Group:Link/Supplier Group:140",
		]
		based_on_details["based_on_select"] = "t1.supplier, t3.supplier_group,"
		based_on_details["based_on_group_by"] = "t1.supplier"
		based_on_details["addl_tables"] = ",`tabSupplier` t3"
		based_on_details["addl_tables_relational_cond"] = " and t1.supplier = t3.name"

	elif based_on == "Supplier Group":
		based_on_details["based_on_cols"] = ["Supplier Group:Link/Supplier Group:140"]
		based_on_details["based_on_select"] = "t3.supplier_group,"
		based_on_details["based_on_group_by"] = "t3.supplier_group"
		based_on_details["addl_tables"] = ",`tabSupplier` t3"
		based_on_details["addl_tables_relational_cond"] = " and t1.supplier = t3.name"

	elif based_on == "Territory":
		based_on_details["based_on_cols"] = ["Territory:Link/Territory:120"]
		based_on_details["based_on_select"] = "t1.territory,"
		based_on_details["based_on_group_by"] = "t1.territory"
		based_on_details["addl_tables"] = ""

	elif based_on == "Project":
		if trans in ["Sales Invoice", "Delivery Note", "Sales Order"]:
			based_on_details["based_on_cols"] = ["Project:Link/Project:120"]
			based_on_details["based_on_select"] = "t1.project,"
			based_on_details["based_on_group_by"] = "t1.project"
			based_on_details["addl_tables"] = ""
		elif trans in ["Purchase Order", "Purchase Invoice", "Purchase Receipt"]:
			based_on_details["based_on_cols"] = ["Project:Link/Project:120"]
			based_on_details["based_on_select"] = "t2.project,"
			based_on_details["based_on_group_by"] = "t2.project"
			based_on_details["addl_tables"] = ""
		else:
			frappe.throw(_("Project-wise data is not available for Quotation"))
	
	elif based_on == "Cost Center":
		based_on_details["based_on_cols"] = ["Cost Center:Link/Cost Center:120"]
		based_on_details["based_on_select"] = "t2.cost_center,"
		based_on_details["based_on_group_by"] = "t2.cost_center"
		based_on_details["addl_tables"] = ""

	return based_on_details
