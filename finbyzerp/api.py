from __future__ import unicode_literals
import frappe
from erpnext.accounts.utils import get_fiscal_year, flt
import datetime
from frappe.utils.background_jobs import enqueue
from frappe.utils import cint, getdate, get_fullname, get_url_to_form,now_datetime,validate_email_address
from frappe.utils.pdf import get_pdf
from frappe.utils.file_manager import save_file
from frappe import _
from frappe.model.mapper import get_mapped_doc


import json
import os
import sys
import time


def before_insert(self, method):
	opening_naming_series(self)

@frappe.whitelist()
def get_project_name():
	frappe.flags.ignore_account_permission = True
	project_name = frappe.db.get_value("Global Defaults", "Global Defaults","project_name")
	
	return {"project_name":project_name}


def sales_invoice_on_submit(self, method):
	if self.get('eway_bill_json_required'):
		if not self.billing_address_gstin:
			frappe.throw("Billing Address GSTIN is required.")
		
		if not self.customer_gstin:
			frappe.throw("Customer GSTIN is required.")
		
		if not self.distance:
			frappe.throw("Distance (in km) is required.")
		
		if self.distance > 4000:
			frappe.throw("Distance cannot be greater than 4000 kms")
		
		if not self.customer_address:
			frappe.throw("Customer Address is required.")

		if self.customer_address:
			if not frappe.db.get_value("Address", self.customer_address, 'pincode'):
				frappe.throw("Customer Postal Code is required.")
		
		for item in self.items:
			if not item.gst_hsn_code and not item.is_non_gst:
				frappe.throw("Row: {} HSN/SAC is reuired for item {}".format(item.idx, item.item_code))
def get_fiscal(date):
	fy = get_fiscal_year(date)[0]
	fiscal = frappe.db.get_value("Fiscal Year", fy, 'fiscal')

	return fiscal if fiscal else fy.split("-")[0][2:] + fy.split("-")[1][2:]

def before_naming(self, method):
	if not self.get('amended_from') and not self.get('name'):
		date = self.get("transaction_date") or self.get("posting_date") or  self.get("manufacturing_date") or self.get('date') or getdate()
		fiscal = get_fiscal(date)
		self.fiscal = fiscal
		if not self.get('company_series'):
			self.company_series = None
		if self.get('series_value'):
			if self.series_value > 0:
				name = naming_series_name(self.naming_series, fiscal, self.company_series)
				check = frappe.db.get_value('Series', name, 'current', order_by="name")
				if check == 0:
					pass
				elif not check:
					frappe.db.sql("insert into tabSeries (name, current) values ('{}', 0)".format(name))

				frappe.db.sql("update `tabSeries` set current = {} where name = '{}'".format(cint(self.series_value) - 1, name))

def naming_series_name(name, fiscal = None, company_series=None):
	if fiscal == None:
		fiscal = ''
	if company_series:
		name = name.replace('company_series', str(company_series))
	
	name = name.replace('YYYY', str(datetime.date.today().year))
	name = name.replace('YY', str(datetime.date.today().year)[2:])
	name = name.replace('MM', '{0:0=2d}'.format(datetime.date.today().month))
	name = name.replace('DD', '{0:0=2d}'.format(datetime.date.today().day))
	name = name.replace('fiscal', str(fiscal))
	name = name.replace('#', '')
	name = name.replace('.', '')
	
	return name

@frappe.whitelist()
def check_counter_series(name, company_series = None, date = None):
	
	if not date:
		date = datetime.date.today()
	
	
	fiscal = get_fiscal(date)
	
	name = naming_series_name(name, fiscal, company_series)
	
	check = frappe.db.get_value('Series', name, 'current', order_by="name")
	
	if check == 0:
		return 1
	elif check == None:
		frappe.db.sql("insert into tabSeries (name, current) values ('{}', 0)".format(name))
		return 1
	else:
		return int(frappe.db.get_value('Series', name, 'current', order_by="name")) + 1

def opening_naming_series(self):
	if not self.name and self.is_opening == "Yes":
		self.naming_series = 'O' + self.naming_series

@frappe.whitelist()
def get_desktop_settings():
	from frappe.config import get_modules_from_all_apps_for_user
	from frappe.desk.moduleview import get_home_settings, get_links
	all_modules = get_modules_from_all_apps_for_user()
	home_settings = get_home_settings()
	# module_map = {'Desk':'/files/desk_icon.png','Users and Permissions':'/files/desk_icon.png','Accounts':'icon finbyz-accounting','Getting Started':'icon finbyz-getting_started'}
	module_map = {'Desk':'icon finbyz-desk','Users and Permissions':'icon finbyz-users-and-permissions', \
		'Accounts':'icon finbyz-accounting','Getting Started':'icon finbyz-getting_started', \
		'Learn': 'icon finbyz-learn','Tools': 'icon finbyz-tools',  'Social': 'icon finbyz-social',  \
		'Leaderboard': 'icon finbyz-leaderboard','dashboard': 'icon finbyz-dashboard', \
		'Selling': 'icon finbyz-selling', 'Buying': 'icon finbyz-buying','Stock': 'icon finbyz-stock',\
		'Assets': 'icon finbyz-assets','Projects': 'icon finbyz-projects','CRM': 'icon finbyz-crm', \
		'Support': 'icon finbyz-support','HR': 'icon finbyz-hr', 'Quality Management': 'icon finbyz-quality-management', \
		'Manufacturing': 'icon finbyz-manufacturing', 'Help': 'icon finbyz-help', 'Chemical': 'icon finbyz-chemical', \
		'Exim': 'icon finbyz-exim', 'Settings' : 'icon finbyz-settings', 'Website' : 'icon finbyz-website', \
		'Customization' : 'icon finbyz-customization','Marketplace': 'icon finbyz-marketplace', \
		'Integrations':'icon finbyz-integrations','Core':'icon finbyz-developer', \
		'Ceramic': 'icon finbyz-ceramic','Finbyzweb': 'icon finbyz-finbyzweb',\
		'Engineering': 'icon finbyz-engineering','Transport':'icon finbyz-transport','Education': 'icon finbyz-education'}

	modules_by_name = {}
	for m in all_modules:
		if m['module_name'] in module_map.keys():
			m['icon'] = module_map[m['module_name']]
		modules_by_name[m['module_name']] = m
	module_categories = ['Modules', 'Domains', 'Places', 'Administration']
	user_modules_by_category = {}

	user_saved_modules_by_category = home_settings.modules_by_category or {}
	user_saved_links_by_module = home_settings.links_by_module or {}

	def apply_user_saved_links(module):
		module = frappe._dict(module)
		all_links = get_links(module.app, module.module_name)
		module_links_by_name = {}
		for link in all_links:
			module_links_by_name[link['name']] = link

		if module.module_name in user_saved_links_by_module:
			user_links = frappe.parse_json(user_saved_links_by_module[module.module_name])
			module.links = [module_links_by_name[l] for l in user_links if l in module_links_by_name]

		return module

	for category in module_categories:
		if category in user_saved_modules_by_category:
			user_modules = user_saved_modules_by_category[category]
			user_modules_by_category[category] = [apply_user_saved_links(modules_by_name[m]) \
				for m in user_modules if modules_by_name.get(m)]
		else:
			user_modules_by_category[category] = [apply_user_saved_links(m) \
				for m in all_modules if m.get('category') == category]

	# filter out hidden modules
	if home_settings.hidden_modules:
		for category in user_modules_by_category:
			hidden_modules = home_settings.hidden_modules or []
			modules = user_modules_by_category[category]
			user_modules_by_category[category] = [module for module in modules if module.module_name not in hidden_modules]

	return user_modules_by_category

@frappe.whitelist()
def get_options_for_global_modules():
	# frappe.msgprint('call')
	from frappe.config import get_modules_from_all_apps
	all_modules = get_modules_from_all_apps()

	blocked_modules = frappe.get_doc('User', 'Administrator').get_blocked_modules()

	module_map = {'Desk':'icon finbyz-desk','Users and Permissions':'icon finbyz-users-and-permissions', \
	'Accounts':'icon finbyz-accounting','Getting Started':'icon finbyz-getting_started', \
	'Learn': 'icon finbyz-learn','Tools': 'icon finbyz-tools',  'Social': 'icon finbyz-social', \
	'Leaderboard': 'icon finbyz-leaderboard','dashboard': 'icon finbyz-dashboard', 'Selling': 'icon finbyz-selling', \
	'Buying': 'icon finbyz-buying','Stock': 'icon finbyz-stock','Assets': 'icon finbyz-assets', \
	'Projects': 'icon finbyz-projects','CRM': 'icon finbyz-crm', 'Support': 'icon finbyz-support',\
	'HR': 'icon finbyz-hr', 'Quality Management': 'icon finbyz-quality-management', \
	'Manufacturing': 'icon finbyz-manufacturing', 'Help': 'icon finbyz-help', 'Chemical': 'icon finbyz-chemical', \
	'Exim': 'icon finbyz-exim','Engineering': 'icon finbyz-engineering','Transport':'icon finbyz-transport'}
	
	# frappe.msgprint(str(all_modules))
	options = []
	for module in all_modules:
		module = frappe._dict(module)
		# frappe.msgprint(str(module))
		options.append({
			'category': module.category,
			'label': module.label,
			'value': module.module_name,
			'checked': module.module_name not in blocked_modules
		})

	return options

def daily_entry_summary_mail():
	if frappe.db.exists("Daily Entry Summary","DES-001"):
		doc = frappe.get_doc("Daily Entry Summary","DES-001")

		recipients = doc.recipient.split(",") if doc.recipient.find(",") != -1 else doc.recipient
		if doc.daily_entry_summary and validate_email_address(recipients):
			message = ""
			for dtype in doc.doctypes:
				body = ''
				total = 0

				table_data = """
					<table class="table table-bordered " style="font-size:100%; float: left;  width:auto; margin:10px 10px 10px 0;">
					<thead><tr><th colspan="2"><b><center>{dtype}</center></b></th></tr></thead>
				""".format(dtype=dtype.document_type)

				query = frappe.db.sql("select owner,count(name) as no_of_entries from `tab{dtype}` where docstatus=1 and CAST(creation AS DATE) = CURDATE() GROUP BY owner".format(dtype=dtype.document_type),as_dict=1)

				if query:
					for data in query:
						total += data.no_of_entries
						user = get_fullname(data.owner)
						body +="""<tr>
									<td><center>{user}</center></td> <td><center><b>{no_of_entries}</b></center></td>
								</tr>
						""".format(user = user,no_of_entries=data.no_of_entries)

					body += """<tr>
								<td><center><b>Total</h5></b><center></td> <td><center><b>{total}</h5></b><center></td>
							</tr>
					""".format(total=total)
				else:
					body += """<tr><td><b><center>0</center></b></td></tr>"""

				table_data += """
							<tbody>{body}</tbody>
					</table>
				""".format(body=body)

				message += """&nbsp;{table_data}&nbsp;
				""".format(table_data=table_data)

			frappe.sendmail(recipients=recipients,
				reference_doctype='User', reference_name="Administrator",
				subject='Daily Entry Summary', message="""<div style="width:100%;">""" + message + """</div>""", now=True)

def daily_transaction_summary_mail():
	if frappe.db.exists("Daily Entry Summary","DES-001"):
		doc = frappe.get_doc("Daily Entry Summary","DES-001")
		recipients = doc.recipient.split(",") if doc.recipient.find(",") != -1 else doc.recipient

		if doc.daily_transaction_summary and validate_email_address(recipients):
			message = ""
			for dtype in doc.doctypes:
				query_col = body = thead = table_data = ''
				total = 0

				query_columns = frappe.db.sql("""select fieldname,label from `tabDocField` where parent='{}' and in_list_view=1 ORDER BY idx""".format(dtype.document_type),as_dict=1)
				thead += """<th><center>Name</center></th>"""

				query_col = "name,"
				for lview in query_columns:
					query_col += "{col},".format(col=lview.fieldname)
					thead += """<th><center>{col}</center></th>""".format(col=lview.label)

				query_columns = query_col[:-1]

				table_data = """<p><h4><b>{dtype}:</b></h4></p></br></br>
					<table class="table table-bordered" style="width:auto;">
					<thead><tr>{thead}</tr></thead>
				""".format(dtype=dtype.document_type,thead=thead)
				
				# select_date = 'transaction_date' if dtype.document_type in ['Purchase Order','Sales Order'] else 'posting_date'
				query = frappe.db.sql("""select {query_columns} from `tab{dtype}` where docstatus = 1 and CAST(creation AS DATE) = CURDATE()""".format(query_columns=query_columns,dtype=dtype.document_type),as_dict=1)
				
				if query:
					for data in query:
						body += "<tr>"
						for key in query_columns.split(","):
							if key == "name":
								url = get_url_to_form(dtype.document_type, data['{key}'.format(key=key)])
								body+= """<td><center><a href={}>{}</a></center></td>""".format(url,data['{key}'.format(key=key)])
							else:
								body += """<td><center>{}</center></td>
							""".format(data['{key}'.format(key=key)])
						body += "</tr>"

				table_data += """
							<tbody>{body}</tbody>
					</table>
				""".format(body=body)

				message += """<br>{table_data}</br>
				""".format(table_data=table_data)
			
			frappe.sendmail(recipients=recipients,
				reference_doctype='User', reference_name="Administrator",
				subject='Daily Transaction Summary', message=message, now=True)


def stock_entry_validate(self, method):
	if self._action == "submit":
		
		validate_additional_cost(self)

def validate_additional_cost(self):
	if self.purpose in ['Repack','Manufacture'] and self._action == "submit":
		if abs(round(flt(self.value_difference,1))) != abs(round(flt(self.total_additional_costs,1))):
			frappe.throw("ValuationError: Value difference between incoming and outgoing amount is higher than additional cost")

def validate_user_mobile_no(self,method):
	if self.mobile_no:
		if not self.mobile_no.isdigit():
			frappe.throw("Please Enter Digits Only in Mobile Number.")
		elif len(self.mobile_no) != 10:
			frappe.throw("Please Enter 10 digit Mobile Number.")

from frappe.core.doctype.report.report import Report

def report_validate(self):
	"""only administrator can save standard report"""
	if not self.module:
		self.module = frappe.db.get_value("DocType", self.ref_doctype, "module")

	if not self.is_standard:
		self.is_standard = "No"
		if frappe.session.user=="Administrator" and getattr(frappe.local.conf, 'developer_mode',0)==1:
			self.is_standard = "Yes"

	if self.is_standard == "No":
		# allow only script manager to edit scripts
		if self.report_type != 'Report Builder':
			frappe.only_for('Script Manager', True)

		if frappe.db.get_value("Report", self.name, "is_standard") == "Yes":
			frappe.throw(_("Cannot edit a standard report. Please duplicate and create a new report"))

	# finbyz Change in if condition
	if self.is_standard == "Yes" and "Local Admin" not in frappe.get_roles(frappe.session.user):
		frappe.throw(_("Only Administrator can save a standard report. Please rename and save."))

	if self.report_type == "Report Builder":
		self.update_report_json()

def customer_validate(self,method):
	set_party_account_based_on_currency(self)

def supplier_validate(self,method):
	set_party_account_based_on_currency(self)

def set_party_account_based_on_currency(self):
	if self.default_currency:
		if self.doctype == "Customer":
			party_type = "Customer"
			account_type = "Receivable"
		else:
			party_type = "Supplier"
			account_type = "Payable"
		if not frappe.db.exists("GL Entry",{'party_type':party_type,'party':self.name}):
			company_currency_list = frappe.get_all("Company",fields=['name','default_currency'])
			account_dict = {}
			if self.accounts:	
				for d in company_currency_list:
					if self.default_currency != d['default_currency']:
						for row in self.accounts:	
							if row.company == d['name']:
								if not frappe.db.exists("Account",{'account_type':account_type,'freeze_account':'No','account_currency':self.default_currency,'company':d['name']}):
									frappe.msgprint("Please create {0} account in {1} for company {2} then try to change currency again".format(account_type,self.default_currency,d['name']))
								else:
									row.account = frappe.db.get_value("Account",{'account_type':account_type,'freeze_account':'No','account_currency':self.default_currency,'company':d['name'],'is_group':0},'name')
							else:
								if not frappe.db.exists("Account",{'account_type':account_type,'freeze_account':'No','account_currency':self.default_currency,'company':d['name'],}):
									frappe.msgprint("Please create {0} account in {1} for company {2} then try to change currency again".format(account_type,self.default_currency,d['name']))
								else:
									account_dict.update({
										'company': d['name'],
										'account': frappe.db.get_value("Account",{'account_type':account_type,'freeze_account':'No','company':d['name'],'account_currency':self.default_currency})
									})
					#frappe.msgprint(str(account_dict))
					if account_dict:
						self.extend('accounts', [account_dict])
			else:
				for d in company_currency_list:
					if self.default_currency != d['default_currency']:
						if frappe.db.exists("Account",{'account_type':account_type,'freeze_account':'No','company':d['name'],'account_currency':self.default_currency}):
							self.append("accounts",{
								'company': d['name'],
								'account':frappe.db.get_value("Account",{'account_type':account_type,'freeze_account':'No','company':d['name'],'account_currency':self.default_currency})
							})
						else:
							frappe.msgprint("Please create {0} account in {1} for company {2} then try to change currency again".format(account_type,self.default_currency,d['name']))

def si_validate(self,method):
	set_account_in_transaction(self)

def pi_validate(self,method):
	set_account_in_transaction(self)

def set_account_in_transaction(self):
	if self.doctype == "Sales Invoice":
		party_type = "Customer"
		party = self.customer
		account_type = "Receivable"
		field = 'debit_to'
	else:
		party_type = "Supplier"
		party = self.supplier
		account_type = "Payable"
		field = 'credit_to'

	if not frappe.db.exists("GL Entry",{'party_type':party_type,'party':party}):
		if field:
			if frappe.db.get_value("Account",field,'account_currency') != self.currency:
				if frappe.db.exists("Account",{'account_type':account_type,'freeze_account':'No','company':self.company,'account_currency':self.currency}):
					field = frappe.db.get_value("Account",{'account_type':account_type,'freeze_account':'No','company':self.company,'account_currency':self.currency})
				else:
					frappe.msgprint("Please create {0} account in {1} for company {2} and set in accounting detail".format(account_type,self.currency,self.company))


@frappe.whitelist()
def make_meetings(source_name, doctype, ref_doctype, target_doc=None):
	def set_missing_values(source, target):
		target.party_type = doctype
		now = now_datetime()
		if ref_doctype == "Meeting Schedule":
			target.scheduled_from = target.scheduled_to = now
		else:
			target.meeting_from = target.meeting_to = now
			if doctype == "Lead":
				target.organization = source.company_name

	def update_contact(source, target, source_parent):
		if doctype == 'Lead':
			if not source.organization_lead:
				target.contact = source.lead_name

	doclist = get_mapped_doc(doctype, source_name, {
			doctype: {
				"doctype": ref_doctype,
				"field_map":  {
					'company_name': 'organization',
					'name': 'party',
					'customer_name':'organization',
					'contact_email':'email_id',
					'contact_mobile':'mobile_no'
				},
				"field_no_map": [
					"naming_series"
				],
				"postprocess": update_contact
			}
		}, target_doc, set_missing_values)

	return doclist
	
