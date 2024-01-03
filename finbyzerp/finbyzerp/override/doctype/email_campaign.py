import frappe
from frappe import _
from frappe.utils import getdate, add_days, today, nowdate, cstr
from frappe.core.doctype.communication.email import make

def send_email_to_leads_or_contacts():
	email_campaigns = frappe.get_all("Email Campaign", filters = { 'status': ('not in', ['Unsubscribed', 'Completed', 'Scheduled']) })
	for camp in email_campaigns:
		email_campaign = frappe.get_doc("Email Campaign", camp.name)
		campaign = frappe.get_cached_doc("Campaign", email_campaign.campaign_name)
		for entry in campaign.get("campaign_schedules"):
			scheduled_date = add_days(email_campaign.get('start_date'), entry.get('send_after_days'))
			if scheduled_date == getdate(today()):
				send_mail(entry, email_campaign)

def send_mail(entry, email_campaign):
	recipient = frappe.db.get_value(email_campaign.email_campaign_for, email_campaign.get("recipient"), 'email_id')

	email_template = frappe.get_doc("Email Template", entry.get("email_template"))
	sender = frappe.db.get_value("User", email_campaign.get("sender"), 'email')
	context = frappe.get_doc(email_campaign.email_campaign_for, email_campaign.recipient)
	content = frappe.render_template(email_template.get("response"), vars(context)) + frappe.db.get_value("User",email_campaign.sender,'email_signature') or "<br><p>FinByz Tech Pvt Ltd</p>"
	# send mail and link communication to document
	comm = make(
		doctype = email_campaign.email_campaign_for, #finbyz change
		name = email_campaign.recipient,#finbyz change
		subject = frappe.render_template(email_template.get("subject"), vars(context)),
		content = content,
		sender = sender,
		recipients = recipient,
		communication_medium = "Email",
		sent_or_received = "Sent",
		send_email = True,
		email_template = email_template.name
	)
	return comm