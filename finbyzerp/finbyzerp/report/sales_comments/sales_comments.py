# Copyright (c) 2013, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe import _
from frappe.utils import getdate, nowdate, date_diff, get_fullname
from frappe.contacts.doctype.contact.contact import get_contact_details, get_default_contact

def execute(filters=None):
	filters.from_date = getdate(filters.from_date or nowdate())
	filters.to_date = getdate(filters.to_date or nowdate())
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data, filters)
	return columns, data, None, chart

	
def get_columns():
	columns = [
		{ "label": _("Ref DocType"),"fieldname": "Ref DocType","fieldtype": "Data","width": 100},
		{ "label": _("Ref DocName"),"fieldname": "Ref DocName","fieldtype": "Dynamic Link","options": "Ref DocType","width": 100},
		{ "label": _("Next Contact Date"),"fieldname": "Next Contact Date","fieldtype": "Date","width": 120},
		{ "label": _("Date"),"fieldname": "Date","fieldtype": "Date","width": 120},
		{ "label": _("Caller"),"fieldname": "Caller","fieldtype": "Data","width": 110},
		{ "label": _("Organization"),"fieldname": "Organization","fieldtype": "Data","width": 180},
		{ "label": _("Person"),"fieldname": "Person","fieldtype": "Data","width": 120},
		{ "label": _("Comment"),"fieldname": "Comment","fieldtype": "Data","width": 400},
		{ "label": _("Mobile"),"fieldname": "Mobile","fieldtype": "Data","width": 100},
		{ "label": _("User"),"fieldname": "User","fieldtype": "Link","options":"User","width": 100},
		# _("Ref DocType") + ":Data:100",
		# _("Ref DocName") + ":Dynamic Link/"+_("Ref DocType")+":100",
		# _("Next Contact Date") + ":Date:120",
		# _("Date") + ":Date:120",
		# _("Caller") + "::110",
		# _("Organization") + "::180",
		# _("Person") + "::120",
		# _("Comment") + ":Data:400",
		# _("Mobile") + "::100",
		# _("User") + ":Link/User:100",
	]
	return columns

def get_data(filters):

	where_clause = ''
	where_clause_for_comment=''
	where_clause += " and co.creation between '%s 00:00:00' and '%s 23:59:59' " % (filters.from_date, filters.to_date)
	where_clause_for_comment+= " and co.creation between '%s 00:00:00' and '%s 23:59:59' " % (filters.from_date, filters.to_date)

	if not filters.doctype:
		ref_doctypes = ["'Lead'", "'Customer'", "'Quotation'", "'Opportunity'", "'Sales Order'", "'Sales Invoice'", "'Delivery Note'"]
	else:
		ref_doctypes = ["'"+filters.doctype+"'"]
		
	where_clause += " and co.parenttype in (%s)" % ",".join(ref_doctypes)
	where_clause_for_comment+=" and co.reference_doctype in (%s)" % ",".join(ref_doctypes)

	if filters.user:
		where_clause += " and co.added_by = '%s' " % filters.user
		where_clause_for_comment+=" and co.owner = '%s' " % filters.user




	data_for_crm_notes = frappe.db.sql(f"""
		SELECT
			co.parenttype as "Ref DocType", co.parent as "Ref DocName", co.added_by as "User", co.creation as "Date", co.note as "Comment", co.added_by as comment_email
		FROM
			`tabCRM Note` as co
		WHERE
			1=1 {where_clause}
		ORDER BY
			co.creation DESC""", as_dict=1)

	data_for_comments = frappe.db.sql("""
		SELECT
			co.reference_doctype as "Ref DocType", co.reference_name as "Ref DocName", co.owner as "User" , co.creation as "Date", co.content as "Comment", co.comment_email
		FROM
			`tabComment` as co
		WHERE
			co.comment_type="Comment"
			%s
		ORDER BY
			co.creation DESC""" % where_clause_for_comment, as_dict=1)

	# Combine data into a dictionary with (Ref DocType, Ref DocName) as the key
	combined_data = {}

	# Append data from data_for_crm_notes
	for row in data_for_crm_notes:
		key = (row["Ref DocType"], row["Ref DocName"])
		if key not in combined_data:
			combined_data[key] = []
		combined_data[key].append(row)

	# Append data from data_for_comments
	for row in data_for_comments:
		key = (row["Ref DocType"], row["Ref DocName"])
		if key not in combined_data:
			combined_data[key] = []
		combined_data[key].append(row)

	# Convert the dictionary values into a flat list
	final_data = [item for sublist in combined_data.values() for item in sublist]

	


	for row in final_data:
		row["Next Contact Date"] = get_next_contact_date(row, filters)
		row["Mobile"] = get_contact(row, filters)
		row["Organization"] = get_organization(row, filters)
		row["Person"] = get_contact_display(row, filters)
		row["Caller"] = get_fullname(row['comment_email'])
	
	return final_data
	
def get_contact(row, filters):

	party_type = filters.doctype or row["Ref DocType"]
	party = row["Ref DocName"]
	
	if party_type in ["Lead", "Customer"]:
		contact_person = get_default_contact(party_type, party)
		
		if not contact_person:
			return None
		
		else:
			return get_contact_details(contact_person)["contact_mobile"]
			
	else:
		contact_mobile = frappe.db.get_value(party_type, party, "contact_mobile") or None
		
		return contact_mobile
	
def get_next_contact_date(row, filters):

	party_type = filters.doctype or row["Ref DocType"]
	party = row["Ref DocName"]
	try:
		next_contact_date = frappe.db.get_value(party_type, party, "contact_date") or None
	except:
		next_contact_date = None
	return next_contact_date

def get_organization(row, filters):
	
	party_type = filters.doctype or row["Ref DocType"]
	party = row["Ref DocName"]
	
	if party_type == "Lead":
		organization = frappe.db.get_value(party_type, party, "company_name")
	
	elif party_type in ["Opportunity", "Customer", "Quotation"]:
		organization = frappe.db.get_value(party_type, party, "customer_name")
	
	else:
		organization = frappe.db.get_value(party_type, party, "customer")
	
	return organization
	
def get_contact_display(row, filters):

	party_type = filters.doctype or row["Ref DocType"]
	party = row["Ref DocName"]
	
	if party_type in ["Lead", "Customer"]:
		contact_person = get_default_contact(party_type, party)
		
		if not contact_person:
			return None
		
		else:
			return get_contact_details(contact_person)["contact_display"]
			
	else:
		contact_display = frappe.db.get_value(party_type, party, "contact_display") or None
		
		return contact_display

def get_chart_data(data, filters):
	count = []
	based_on, date_range = None, None
	period = {"Day": "%d", "Week": "%W", "Month": "%m"}
	from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)
	labels = list()
	diff = date_diff(filters.to_date, filters.from_date)
	
	if diff <= 30:
		based_on = "Day"
		date_range = diff
	elif diff <= 90 and diff > 30:
		based_on = "Week"
		date_range = int(to_date.strftime(period[based_on])) - int(from_date.strftime(period[based_on]))
	elif diff > 90:
		based_on = "Month"
		date_range = int(to_date.strftime(period[based_on])) - int(from_date.strftime(period[based_on]))
		
	if based_on == "Day":
		for d in range(date_range+1):
			cnt = 0
			date = from_date + datetime.timedelta(days=d)
			for row in data:
				sql_date = getdate(row["Date"])
				if date == sql_date:
					cnt += 1
			
			count.append(cnt)
			labels.append(date.strftime("%d-%b '%y"))
	
	else:
		period_date = dict()
		for x in range(date_diff(to_date, from_date)+1):
			tmp_date = from_date + datetime.timedelta(days=x)
			tmp_period = str(tmp_date.strftime("%y-"+period[based_on]))
			if tmp_period not in period_date:
				period_date[tmp_period] = [tmp_date]
			else:
				period_date[tmp_period].append(tmp_date)
		
		for key, values in sorted(period_date.items()):
			cnt = 0
			for date in values:
				for row in data:
					sql_date = getdate(row["Date"])
					if date == sql_date:
						cnt += 1
						
			count.append(cnt)
			labels.append(values[0].strftime("%d-%b '%y") + " to " + values[-1].strftime("%d-%b '%y"))
	
	datasets = []
	
	if count:
		datasets.append({
			'title': "Total",
			'values': count
		})
	
	chart = {
		"data": {
			'labels': labels,
			'datasets': datasets
		}
	}
	chart["type"] = "bar"
	return chart