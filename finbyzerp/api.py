import frappe
from erpnext.accounts.utils import get_fiscal_year
from erpnext.stock.doctype.repost_item_valuation.repost_item_valuation import execute_repost_item_valuation
from frappe.model.mapper import get_mapped_doc
from frappe.utils import now_datetime


def get_fiscal(date):
	fy = get_fiscal_year(date)[0]
	fiscal = frappe.db.get_value("Fiscal Year", fy, "fiscal")

	return fiscal if fiscal else fy.split("-")[0][2:] + fy.split("-")[1][2:]


def get_naming_series_name(name, fiscal=None, company_series=None):
	today = now_datetime().date()

	if fiscal == None:
		fiscal = ""
	if company_series:
		name = name.replace("company_series", str(company_series))

	name = name.replace("YYYY", str(today.year))
	name = name.replace("YY", str(today.year)[2:])
	name = name.replace("MM", "{0:0=2d}".format(today.month))
	name = name.replace("DD", "{0:0=2d}".format(today.day))
	name = name.replace("fiscal", str(fiscal))
	name = name.replace("#", "")
	name = name.replace(".", "")
	return name


@frappe.whitelist()
def check_counter_series(name, company_series=None, date=None):
	if not date:
		date = now_datetime().date()
	fiscal = get_fiscal(date)
	name = get_naming_series_name(name, fiscal, company_series)
	check = frappe.db.get_value("Series", name, "current", order_by="name")
	if check == 0:
		return 1
	elif check is None:
		frappe.db.sql(f"INSERT INTO `tabSeries` (name, current) values ('{name}', 0)")
		return 1
	else:
		return int(frappe.db.get_value("Series", name, "current", order_by="name")) + 1

# email templates

def sales_invoice_payment_remainder():
	frappe.enqueue(send_sales_invoice_mails, queue='long', timeout=5000, job_name='Payment Reminder Mails')
	return "Payment Reminder Mails Send"


def send_sales_invoice_mails():
	account_settings = frappe.get_doc("Accounts Settings")

	if not account_settings.send_overdue_reminder:
		return

	data = frappe.get_all("Sales Invoice", filters={
			'status': ['in', ('Overdue')],
			'outstanding_amount':(">", 5000),
			'docstatus': 1,
			'is_opening': 'No',
		},
		order_by='posting_date',
		group_by= "customer,company",
		fields=["group_concat(name) as name", "customer", "company"]
	)
	if not frappe.db.exists("Email Template", "Payment Reminder"):
		return "hello"
	email_template = frappe.get_doc("Email Template", "Payment Reminder")

	if account_settings.send_testing_overdue_mail:
		recipients = ",".join([row.email_id for row in account_settings.test_recipients_emails])
		
	for d in data:
		sender = frappe.db.get_value("Company",d.company,"send_from_overdue_email")
		
		if not sender:
			continue
		
		context = {"customer": d.customer, "company": d.company}
		context['sales_invoices'] = [frappe.get_doc("Sales Invoice", name) for name in d.name.split(",")]

		recipients_emails = ",".join([doc.email for doc in context['sales_invoices'] if doc.email and doc.email.replace(" ", "")])
		emails = ",".join(sorted(list(set(recipients_emails.split(",")))))
		
		if not account_settings.send_testing_overdue_mail:
			if not recipients_emails:
				continue
			recipients = emails
		else:
			context["emails"] = emails

		frappe.sendmail(
			recipients=recipients,
			sender=sender,
			subject=frappe.render_template(email_template.subject, context),
			message=frappe.render_template(email_template.response_html, context),
		)
	return "Payment Reminder Mails Send"