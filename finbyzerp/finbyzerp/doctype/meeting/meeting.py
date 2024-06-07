# -*- coding: utf-8 -*-
# Copyright (c) 2017, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import msgprint, db, _
import json
from frappe.utils import cint, getdate, get_fullname, get_url_to_form,now_datetime, get_datetime
# from erpnext.accounts.party import get_party_details
from finbyzerp.finbyzerp.doctype.meeting_schedule.meeting_schedule import get_party_details

class Meeting(Document):
	def validate(self):
		if self.party_type and self.party:
			data = get_party_details(party_type=self.party_type,party=self.party)
			if data:
				self.contact_person = data.contact_person
				self.email_id = data.contact_email
				self.mobile_no = data.contact_mobile
				self.contact = data.contact_dispaly
				self.address = data.customer_address
				self.address_display = data.address_display
				self.organization = data.organisation

		self.check_min_participants()

	def on_submit(self):
		user_name = frappe.db.get_value("Employee",{"user_id":frappe.session.user},"employee_name")
		url = get_url_to_form("Meeting", self.name)
		# url = "http://erp.finbyz.in/desk#Form/Lead%20Meeting/" + self.name
		if user_name:
			discussed = "<strong><a href="+url+">"+self.name+"</a>: </strong>"+ user_name + " Met "+ str(self.contact_person) + " On "+ self.meeting_from +"<br>" + self.discussion.replace('\n', "<br>")
		else:
			discussed = "<strong><a href="+url+">"+self.name+"</a>: </strong>"+ frappe.session.user + " Met "+ str(self.contact_person)+ " On "+ self.meeting_from +"<br>" + self.discussion.replace('\n', "<br>")

		cm = frappe.new_doc("Comment")
		cm.subject = self.name
		cm.comment_type = "Comment"
		cm.content = discussed
		cm.reference_doctype = self.party_type
		cm.reference_name = self.party
		cm.comment_email = frappe.session.user
		cm.comment_by = user_name
		cm.save(ignore_permissions=True)
		if self.party_type == "Lead":
			target_lead = frappe.get_doc("Lead", self.party)
			target_lead.status = "Meeting Done"
			target_lead.turnover = self.turnover
			target_lead.industry = self.industry
			target_lead.business_specifics = self.business_specifics
			target_lead.contact_by = self.contact_by
			target_lead.contact_date = self.contact_date
			if not target_lead.email_id:
				target_lead.email_id = self.email_id
			if not target_lead.lead_name:
				target_lead.lead_name = self.contact_person
			if not target_lead.mobile_no:
				target_lead.mobile_no = self.mobile_no
			target_lead.save(ignore_permissions=True)
		
		# When submit the Meeting then will create the Event
		for d in self.get('actionables'):
			if d.expected_completion_date:
				date_obj = get_datetime(d.expected_completion_date)
				starts_on = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
				ends_on = date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)
				new_event = frappe.get_doc(dict(
					doctype = 'Event',
					subject = d.actionable +' - '+ d.responsible,
					event_category = "Meeting",
					event_type = d.event_type,
					starts_on = starts_on,
					ends_on = ends_on,
					description = self.discussion
				))
				new_event.append('event_participants', {
					'reference_doctype': "Meeting", 'reference_docname': self.name
					})
				new_event.save(ignore_permissions=True)

		self.check_min_participants()

	def check_min_participants(self):
		if self.internal_meeting == 1:
			if len(self.get('meeting_company_representative')) < 2:
				frappe.throw(_("Please add atleast two Participants"))


@frappe.whitelist()
def get_events(start, end, filters=None):
	"""Returns events for Gantt / Calendar view rendering.
	:param start: Start date-time.
	:param end: End date-time.
	:param filters: Filters (JSON).
	"""
	#filters = json.loads(filters)
	from frappe.desk.calendar import get_event_conditions
	conditions = get_event_conditions("Meeting", filters)

	data = frappe.db.sql("""
			select 
				name, meeting_from, meeting_to, organization, party
			from 
				`tabMeeting`
			where
				(meeting_from <= %(end)s and meeting_to >= %(start)s) {conditions}
			""".format(conditions=conditions),
				{
					"start": start,
					"end": end
				}, as_dict=True, update={"allDay": 0})

	if not data:
		return []
		
	data = [x.name for x in data]

	return frappe.db.get_list("Meeting",
		{ "name": ("in", data), "docstatus":1 },
		["name", "meeting_from", "meeting_to", "organization", "party"]
	)