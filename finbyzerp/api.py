from __future__ import unicode_literals
from json import loads
import frappe
from erpnext.accounts.utils import get_fiscal_year, flt
import datetime
from frappe.utils.background_jobs import enqueue
from frappe.utils import cint,cstr, getdate, get_fullname, get_url_to_form,now_datetime,validate_email_address,now

from frappe.utils.pdf import get_pdf
from frappe.utils.file_manager import save_file
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.model.meta import get_field_precision
from erpnext.accounts.utils import get_stock_accounts,get_stock_and_account_balance

from frappe.utils.data import (nowdate,add_to_date,get_first_day_of_week,get_last_day_of_week,get_first_day,get_last_day,
        get_quarter_start,get_quarter_ending,get_year_start,get_year_ending)

from frappe.workflow.doctype.workflow_action.workflow_action import (
    get_common_email_args, deduplicate_actions, clear_workflow_actions, get_next_possible_transitions, get_doc_workflow_state,
    is_workflow_action_already_created, update_completed_workflow_actions, clear_old_workflow_actions_using_user, get_users_next_action_data)
from frappe.desk.doctype.notification_log.notification_log import make_notification_logs
from frappe.utils.background_jobs import enqueue
from frappe.model.workflow import get_workflow_name, send_email_alert
from frappe.desk.notifications import clear_doctype_notifications
from frappe.workflow.doctype.workflow_action.workflow_action import create_workflow_actions_for_roles

import json
import os
import sys
import time
from erpnext.stock.doctype.repost_item_valuation.repost_item_valuation import execute_repost_item_valuation
from erpnext.controllers.sales_and_purchase_return import *
from frappe.desk.desktop import Workspace
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice
from erpnext.buying.doctype.purchase_order.purchase_order import set_missing_values
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.accounts.party import get_party_account
from frappe.contacts.doctype.address.address import get_company_address
from frappe.model.utils import get_fetch_values

# @frappe.whitelist()
# def get_project_name():
# 	frappe.flags.ignore_account_permission = True
# 	project_name = frappe.db.get_value("Global Defaults", "Global Defaults","project_name")
    
# 	return {"project_name":project_name}


# def sales_invoice_on_submit(self, method):
# 	if self.get('eway_bill_json_required'):
# 		if not self.billing_address_gstin:
# 			frappe.throw("Billing Address GSTIN is required.")
        
# 		if not self.customer_gstin:
# 			frappe.throw("Customer GSTIN is required.")
        
# 		if not self.distance:
# 			frappe.throw("Distance (in km) is required.")
        
# 		if self.distance > 4000:
# 			frappe.throw("Distance cannot be greater than 4000 kms")
        
# 		if not self.customer_address:
# 			frappe.throw("Customer Address is required.")

# 		if self.customer_address:
# 			if not frappe.db.get_value("Address", self.customer_address, 'pincode'):
# 				frappe.throw("Customer Postal Code is required.")
        
# 		for item in self.items:
# 			if not item.gst_hsn_code and not item.is_non_gst:
# 				frappe.throw("Row: {} HSN/SAC is reuired for item {}".format(item.idx, item.item_code))
def get_fiscal(date):
    fy = get_fiscal_year(date)[0]
    fiscal = frappe.db.get_value("Fiscal Year", fy, 'fiscal')

    return fiscal if fiscal else fy.split("-")[0][2:] + fy.split("-")[1][2:]
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


def stock_entry_validate(self, method):
    pass
        
def stock_entry_on_submit(self,method):
    validate_additional_cost(self)

def validate_additional_cost(self):
    if self.purpose in ['Repack','Manufacture']:
        diff = abs(round(flt(self.value_difference,1)) - (round(flt(self.total_additional_costs,1))))
        if diff > 5:
            frappe.throw("ValuationError: Value difference between incoming and outgoing amount is higher than additional cost")

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

def validate_item_rate(self):
    for row in self.items:
        if row.rate==0 and row.allow_zero_valuation_rate!=1:
            frappe.throw("Rate is mandatory for {} in Row: {}".format(row.item_code,frappe.bold(row.idx)))


def pr_validate(self,method):
    validate_item_rate(self)

@frappe.whitelist()
def make_meetings(source_name, doctype, ref_doctype, target_doc=None):
    def set_missing_values(source, target):
        target.party_type = doctype
        target.party = source_name
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
                    'customer_name':'organization',
                    'contact_email':'email_id',
                    'contact_mobile':'mobile_no'
                },
                "field_no_map": [
                    "naming_series",
                    "lead",
                    "customer",
                    "opportunity"
                ],
                "postprocess": update_contact
            }
        }, target_doc, set_missing_values)

    return doclist
    

import os

def get_doc_files(files, start_path):
    """walk and sync all doctypes and pages"""

    if not files:
        files = []

    # load in sequence - warning for devs
    document_types = ['doctype', 'page', 'report', 'dashboard_chart_source', 'print_format',
        'website_theme', 'web_form', 'web_template', 'notification', 'print_style',
        'data_migration_mapping', 'data_migration_plan',
        'onboarding_step', 'module_onboarding']

    for doctype in document_types:
        doctype_path = os.path.join(start_path, doctype)
        if os.path.exists(doctype_path):
            for docname in os.listdir(doctype_path):
                if os.path.isdir(os.path.join(doctype_path, docname)):
                    doc_path = os.path.join(doctype_path, docname, docname) + ".json"
                    if os.path.exists(doc_path):
                        if not doc_path in files:
                            files.append(doc_path)

    return files

def finbyz_future_sle_exists(args):
    return frappe.db.sql("""
        select name
        from `tabStock Ledger Entry`
        where
            warehouse = '{}' and item_code = '{}'
            and timestamp(posting_date, posting_time)
                >= timestamp('{}','{}')
            and voucher_no != '{}'
            and is_cancelled = 0
        limit 1
        """.format(args.warehouse,args.item_code,args.posting_date,args.posting_time,args.voucher_no))

def check_if_stock_and_account_balance_synced(posting_date, company, voucher_type=None, voucher_no=None):
    if not cint(erpnext.is_perpetual_inventory_enabled(company)):
        return

    accounts = get_stock_accounts(company, voucher_type, voucher_no)
    stock_adjustment_account = frappe.db.get_value("Company", company, "stock_adjustment_account")

    for account in accounts:
        account_bal, stock_bal, warehouse_list = get_stock_and_account_balance(account,
            posting_date, company)

        if abs(account_bal - stock_bal) > 5:
            precision = get_field_precision(frappe.get_meta("GL Entry").get_field("debit"),
                currency=frappe.get_cached_value('Company',  company,  "default_currency"))

            diff = flt(stock_bal - account_bal, precision)

            error_reason = _("Stock Value ({0}) and Account Balance ({1}) are out of sync for account {2} and it's linked warehouses as on {3}.").format(
                stock_bal, account_bal, frappe.bold(account), posting_date)
            error_resolution = _("Please create an adjustment Journal Entry for amount {0} on {1}")\
                .format(frappe.bold(diff), frappe.bold(posting_date))

            frappe.msgprint(
                msg="""{0}<br></br>{1}<br></br>""".format(error_reason, error_resolution),
                raise_exception=StockValueAndAccountBalanceOutOfSync,
                title=_('Values Out Of Sync'),
                primary_action={
                    'label': _('Make Journal Entry'),
                    'client_action': 'erpnext.route_to_adjustment_jv',
                    'args': get_journal_entry(account, stock_adjustment_account, diff)
                })


def get_timespan_date_range(timespan):
    today = nowdate()
    date_range_map = {
        "last week": lambda: (get_first_day_of_week(add_to_date(today, days=-7)), get_last_day_of_week(add_to_date(today, days=-7))),
        "last month": lambda: (get_first_day(add_to_date(today, months=-1)), get_last_day(add_to_date(today, months=-1))),
        "last quarter": lambda: (get_quarter_start(add_to_date(today, months=-3)), get_quarter_ending(add_to_date(today, months=-3))),
        "last 6 months": lambda: (get_quarter_start(add_to_date(today, months=-6)), get_quarter_ending(add_to_date(today, months=-3))),
        "last year": lambda: (get_year_start(add_to_date(today, years=-1)), get_year_ending(add_to_date(today, years=-1))),
        "yesterday": lambda: (add_to_date(today, days=-1),) * 2,
        "today": lambda: (today, today),
        "tomorrow": lambda: (add_to_date(today, days=1),) * 2,
        # "this week": lambda: (get_first_day_of_week(today), today),
        "this week": lambda: (get_first_day_of_week(today), get_last_day_of_week(get_first_day_of_week(today))),
        # "this month": lambda: (get_first_day(today), today),
        "this month": lambda: (get_first_day(today), get_last_day(get_first_day(today))),
        # "this quarter": lambda: (get_quarter_start(today), today),
        "this quarter": lambda: (get_quarter_start(today), get_quarter_ending(get_quarter_start(today))),
        # "this year": lambda: (get_year_start(today), today),
        "this year": lambda: (get_year_start(today), get_year_ending(get_year_start(today))),
        "next week": lambda: (get_first_day_of_week(add_to_date(today, days=7)), get_last_day_of_week(add_to_date(today, days=7))),
        "next month": lambda: (get_first_day(add_to_date(today, months=1)), get_last_day(add_to_date(today, months=1))),
        "next quarter": lambda: (get_quarter_start(add_to_date(today, months=3)), get_quarter_ending(add_to_date(today, months=3))),
        "next 6 months": lambda: (get_quarter_start(add_to_date(today, months=3)), get_quarter_ending(add_to_date(today, months=6))),
        "next year": lambda: (get_year_start(add_to_date(today, years=1)), get_year_ending(add_to_date(today, years=1))),
    }

    if timespan in date_range_map:
        return date_range_map[timespan]()


def get_date_range(operator, value):
    timespan_map = {
        '1 week': 'week',
        '1 month': 'month',
        '3 months': 'quarter',
        '6 months': '6 months',
        '1 year': 'year',
    }
    period_map = {
        'previous': 'last',
        'next': 'next',
    }

    timespan = period_map[operator] + ' ' + timespan_map[value] if operator != 'timespan' else value

    return get_timespan_date_range(timespan)

@frappe.whitelist()
def repost_transaction_entries():
    execute_repost_item_valuation()

def process_workflow_actions(doc, state):
    workflow = get_workflow_name(doc.get("doctype"))
    if not workflow:
        return

    if state == "on_trash":
        clear_workflow_actions(doc.get("doctype"), doc.get("name"))
        return

    if is_workflow_action_already_created(doc):
        return

    update_completed_workflow_actions(
        doc, workflow=workflow, workflow_state=get_doc_workflow_state(doc)
    )
    clear_doctype_notifications("Workflow Action")

    next_possible_transitions = get_next_possible_transitions(
        workflow, get_doc_workflow_state(doc), doc
    )

    if not next_possible_transitions:
        return

    user_data_map, roles = get_users_next_action_data(next_possible_transitions, doc)

    if not user_data_map:
        return

    create_workflow_actions_for_roles(roles, doc)

    if send_email_alert(workflow):
        enqueue(
            send_workflow_action_email, queue="short", users_data=list(user_data_map.values()), doc=doc
        )


def send_workflow_action_email(users_data, doc):
    common_args = get_common_email_args(doc)
    message = common_args.pop("message", None)
    user_list = []
    for d in users_data:
        email_args = {
            "recipients": [d.get("email")],
            "args": {"actions": list(deduplicate_actions(d.get("possible_actions"))), "message": message},
            "reference_name": doc.name,
            "reference_doctype": doc.doctype,
        }
        email_args.update(common_args)
        if frappe.db.exists("User",d.get("email")):
            user_list.append(d.get("email"))
        enqueue(method=frappe.sendmail, queue="short", **email_args)
    notification_doc = frappe._dict({
        'type': 'Workflow Alert',
        'document_type': doc.doctype,
        'document_name': doc.name,
        'subject': f"{doc.name} Status Has been updated to {doc.workflow_state}",
        'from_user': doc.owner
    })
    make_notification_logs(notification_doc, user_list)

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
                if d.stock_qty>0:
                    d.stock_qty=(-1)*(d.stock_qty)
                validate_quantity(doc, d.item_code, d, ref, valid_items, already_returned_items)

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


def is_workspace_manager():
    return "Workspace Manager" in frappe.get_roles()

@frappe.whitelist()
def new_page(new_page):
    if not loads(new_page):
        return

    page = loads(new_page)

    if page.get("public") and not is_workspace_manager():
        return

    doc = frappe.new_doc("Workspace")
    doc.title = page.get("title")
    doc.module_icon = page.get("module_icon")
    doc.icon = page.get("icon")
    doc.content = page.get("content")
    doc.parent_page = page.get("parent_page")
    doc.label = page.get("label")
    doc.for_user = page.get("for_user")
    doc.public = page.get("public")
    doc.sequence_id = last_sequence_id(doc) + 1
    doc.save(ignore_permissions=True)

    return doc

def last_sequence_id(doc):
    doc_exists = frappe.db.exists(
        {"doctype": "Workspace", "public": doc.public, "for_user": doc.for_user}
    )

    if not doc_exists:
        return 0

    return frappe.get_all(
        "Workspace",
        fields=["sequence_id"],
        filters={"public": doc.public, "for_user": doc.for_user},
        order_by="sequence_id desc",
    )[0].sequence_id

@frappe.whitelist()
def update_page(name, title, icon, parent, public,module_icon):
    public = frappe.parse_json(public)

    doc = frappe.get_doc("Workspace", name)

    filters = {"parent_page": doc.title, "public": doc.public}
    child_docs = frappe.get_list("Workspace", filters=filters)

    if doc:
        doc.title = title
        doc.icon = icon
        doc.parent_page = parent
        doc.module_icon = module_icon
        if doc.public != public:
            doc.sequence_id = frappe.db.count("Workspace", {"public": public}, cache=True)
            doc.public = public
        doc.for_user = "" if public else doc.for_user or frappe.session.user
        doc.label = new_name = f"{title}-{doc.for_user}" if doc.for_user else title
        doc.save(ignore_permissions=True)

        if name != new_name:
            rename_doc("Workspace", name, new_name, force=True, ignore_permissions=True)

        # update new name and public in child pages
        if child_docs:
            for child in child_docs:
                child_doc = frappe.get_doc("Workspace", child.name)
                child_doc.parent_page = doc.title
                if child_doc.public != public:
                    child_doc.public = public
                child_doc.for_user = "" if public else child_doc.for_user or frappe.session.user
                child_doc.label = new_child_name = (
                    f"{child_doc.title}-{child_doc.for_user}" if child_doc.for_user else child_doc.title
                )
                child_doc.save(ignore_permissions=True)

                if child.name != new_child_name:
                    rename_doc("Workspace", child.name, new_child_name, force=True, ignore_permissions=True)

    return {"name": title, "public": public, "label": new_name}

@frappe.whitelist()
def duplicate_page(page_name, new_page):
    if not loads(new_page):
        return

    new_page = loads(new_page)

    if new_page.get("is_public") and not is_workspace_manager():
        return

    old_doc = frappe.get_doc("Workspace", page_name)
    doc = frappe.copy_doc(old_doc)
    doc.title = new_page.get("title")
    doc.icon = new_page.get("icon")
    doc.module_icon = new_page.get("module_icon")
    doc.parent_page = new_page.get("parent") or ""
    doc.public = new_page.get("is_public")
    doc.for_user = ""
    doc.label = doc.title
    doc.module = ""
    if not doc.public:
        doc.for_user = doc.for_user or frappe.session.user
        doc.label = f"{doc.title}-{doc.for_user}"
    doc.name = doc.label
    if old_doc.public == doc.public:
        doc.sequence_id += 0.1
    else:
        doc.sequence_id = last_sequence_id(doc) + 1
    doc.insert(ignore_permissions=True)

    return doc

@frappe.whitelist()
def get_workspace_sidebar_items():
    """Get list of sidebar items for desk"""
    has_access = "Workspace Manager" in frappe.get_roles()

    # don't get domain restricted pages
    blocked_modules = frappe.get_doc("User", frappe.session.user).get_blocked_modules()
    blocked_modules.append("Dummy Module")

    filters = {
        "restrict_to_domain": ["in", frappe.get_active_domains()],
        "module": ["not in", blocked_modules],
    }

    if has_access:
        filters = []

    # pages sorted based on sequence id
    order_by = "sequence_id asc"
    fields = ["name", "title", "for_user", "parent_page", "content", "public", "module", "icon","module_icon"]
    all_pages = frappe.get_all(
        "Workspace", fields=fields, filters=filters, order_by=order_by, ignore_permissions=True
    )
    pages = []
    private_pages = []

    # Filter Page based on Permission
    for page in all_pages:
        try:
            workspace = Workspace(page, True)
            if has_access or workspace.is_permitted():
                if page.public:
                    pages.append(page)
                elif page.for_user == frappe.session.user:
                    private_pages.append(page)
                page["label"] = _(page.get("name"))
        except frappe.PermissionError:
            pass
    if private_pages:
        pages.extend(private_pages)

    return {"pages": pages, "has_access": has_access}


import frappe
import frappe.utils.user
from frappe.model import data_fieldtypes
from frappe.permissions import rights
#permition to local admin
def execute(filters=None):
    frappe.only_for(["System Manager" , "Local Admin"])

    user, doctype, show_permissions = (
        filters.get("user"),
        filters.get("doctype"),
        filters.get("show_permissions"),
    )

    columns, fields = get_columns_and_fields(doctype)
    data = frappe.get_list(doctype, fields=fields, as_list=True, user=user)

    if show_permissions:
        columns = columns + [frappe.unscrub(right) + ":Check:80" for right in rights]
        data = list(data)
        for i, doc in enumerate(data):
            permission = frappe.permissions.get_doc_permissions(frappe.get_doc(doctype, doc[0]), user)
            data[i] = doc + tuple(permission.get(right) for right in rights)

    return columns, data

def get_columns_and_fields(doctype):
    columns = [f"Name:Link/{doctype}:200"]
    fields = ["`name`"]
    for df in frappe.get_meta(doctype).fields:
        if df.in_list_view and df.fieldtype in data_fieldtypes:
            fields.append(f"`{df.fieldname}`")
            fieldtype = f"Link/{df.options}" if df.fieldtype == "Link" else df.fieldtype
            columns.append(
                "{label}:{fieldtype}:{width}".format(
                    label=df.label, fieldtype=fieldtype, width=df.width or 100
                )
            )

    return columns, fields

from frappe.permissions import setup_custom_perms
def add_permission(doctype, role, permlevel=0, ptype=None):
    """Add a new permission rule to the given doctype
    for the given Role and Permission Level"""
    from frappe.core.doctype.doctype.doctype import validate_permissions_for_doctype

    setup_custom_perms(doctype)
    if frappe.db.get_value(
        "Custom DocPerm", dict(parent=doctype, role=role, permlevel=permlevel, if_owner=1)
    ):
        return

    if not ptype:
        ptype = "read"

    custom_docperm = frappe.get_doc(
        {
            "doctype": "Custom DocPerm",
            "__islocal": 1,
            "parent": doctype,
            "parenttype": "DocType",
            "parentfield": "permissions",
            "role": role,
            "permlevel": permlevel,
            ptype: 1,
        }
    )
    custom_docperm.flags.ignore_permissions = True
    custom_docperm.save()

    validate_permissions_for_doctype(doctype)
    return custom_docperm.name


def patch_for_system():

    item_data = frappe.db.sql("""
        SELECT item_code, warehouse, company from `tabStock Ledger Entry` where batch_no is NOT NULL GROUP BY item_code, warehouse
    """, as_dict = 1)

    for row in item_data:
        print(row.item_code,row.warehouse)
        doc = frappe.new_doc("Repost Item Valuation")
        doc.based_on = "Item and Warehouse"
        doc.item_code = row.item_code
        doc.warehouse = row.warehouse
        doc.posting_date = "2023-04-01"
        doc.company = row.company
        doc.status = "Queued"
        doc.save()
        doc.submit()
        print(doc.name)

def get_rounded_tax_amount(itemised_tax, precision):
    # Rounding based on tax_amount precision
    for taxes in itemised_tax.values():
        for tax_account in taxes:
            taxes[tax_account]["tax_amount"] = flt(taxes[tax_account]["tax_amount"], precision)

def set_qty_as_per_stock_uom(self):
    conversion_factor = frappe.db.get_single_value("Stock Settings", "calculate_conversion_factor_based_on_stock_quantity_and_quantity")
    for d in self.get("items"):
        if d.meta.get_field("stock_qty"):
            # Check if item code is present
            # Conversion factor should not be mandatory for non itemized items
            if not d.conversion_factor and d.item_code:
                frappe.throw(_("Row {0}: Conversion Factor is mandatory").format(d.idx))
            if conversion_factor == 0:
                d.stock_qty = flt(d.qty) * flt(d.conversion_factor)

                if self.doctype == "Purchase Receipt" and d.meta.get_field("received_stock_qty"):
                    # Set Received Qty in Stock UOM
                    d.received_stock_qty = flt(d.received_qty) * flt(
                        d.conversion_factor, d.precision("conversion_factor")
                    )


@frappe.whitelist()
def make_purchase_invoice(source_name, target_doc=None):
    return get_mapped_purchase_invoice(source_name, target_doc)

def get_mapped_purchase_invoice(source_name, target_doc=None, ignore_permissions=False):
    def postprocess(source, target):
        target.flags.ignore_permissions = ignore_permissions
        set_missing_values(source, target)
        # Get the advance paid Journal Entries in Purchase Invoice Advance
        if target.get("allocate_advances_automatically"):
            target.set_advances()

        target.set_payment_schedule()
        target.credit_to = get_party_account("Supplier", source.supplier, source.company)

    def update_item(obj, target, source_parent):
        target.amount = flt(obj.amount) - flt(obj.billed_amt)
        target.base_amount = target.amount * flt(source_parent.conversion_rate)
        target.qty = (
            target.amount / flt(obj.rate) if (flt(obj.rate) and flt(obj.billed_amt)) else flt(obj.qty)
        )

        item = get_item_defaults(target.item_code, source_parent.company)
        item_group = get_item_group_defaults(target.item_code, source_parent.company)
        target.cost_center = (
            obj.cost_center
            or frappe.db.get_value("Project", obj.project, "cost_center")
            or item.get("buying_cost_center")
            or item_group.get("buying_cost_center")
        )

    fields = {
        "Purchase Order": {
            "doctype": "Purchase Invoice",
            "field_map": {
                "party_account_currency": "party_account_currency",
                "supplier_warehouse": "supplier_warehouse",
                "payment_terms_template": "payment_terms_template",
            },
            "validation": {
                "docstatus": ["=", 1],
            },
        },
        "Purchase Order Item": {
            "doctype": "Purchase Invoice Item",
            "field_map": {
                "name": "po_detail",
                "parent": "purchase_order",
                "wip_composite_asset": "wip_composite_asset",
            },
            "postprocess": update_item,
            "condition": lambda doc: (doc.base_amount == 0 or abs(doc.billed_amt) < abs(doc.amount)),
        },
        "Purchase Receipt":{
            "doctype":"Payment Schedule",
            "field_map":{
                "name":"payment_schedule",
                "payment_term":"payment_term",
                "due_date":"due_date",
                "invoice_portion":"invoice_portion",
                "discount_type":"discount_type",
                "discount":"discount",
                "payment_amount":"payment_amount",
                "base_payment_amount":"base_payment_amount",
                "outstanding":"outstanding"
            }
        },
        "Purchase Taxes and Charges": {"doctype": "Purchase Taxes and Charges", "add_if_empty": True},
    }

    doc = get_mapped_doc(
        "Purchase Order",
        source_name,
        fields,
        target_doc,
        postprocess,
        ignore_permissions=ignore_permissions,
    )

    return doc


@frappe.whitelist()
def make_purchase_receipt(source_name, target_doc=None):
    def update_item(obj, target, source_parent):
        target.qty = flt(obj.qty) - flt(obj.received_qty)
        target.stock_qty = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.conversion_factor)
        target.amount = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.rate)
        target.base_amount = (
            (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.rate) * flt(source_parent.conversion_rate)
        )

    doc = get_mapped_doc(
        "Purchase Order",
        source_name,
        {
            "Purchase Order": {
                "doctype": "Purchase Receipt",
                "field_map": {"supplier_warehouse": "supplier_warehouse"},
                "validation": {
                    "docstatus": ["=", 1],
                },
            },
            "Purchase Order Item": {
                "doctype": "Purchase Receipt Item",
                "field_map": {
                    "name": "purchase_order_item",
                    "parent": "purchase_order",
                    "bom": "bom",
                    "material_request": "material_request",
                    "material_request_item": "material_request_item",
                    "sales_order": "sales_order",
                    "sales_order_item": "sales_order_item",
                    "wip_composite_asset": "wip_composite_asset",
                },
                "postprocess": update_item,
                "condition": lambda doc: abs(doc.received_qty) < abs(doc.qty)
                and doc.delivered_by_supplier != 1,
            },
            "Payment Schedule":{
            "doctype":"Payment Schedule",
            "field_map":{
                "name":"payment_schedule",
                "payment_term":"payment_term",
                "due_date":"due_date",
                "invoice_portion":"invoice_portion",
                "discount_type":"discount_type",
                "discount":"discount",
                "payment_amount":"payment_amount",
                "base_payment_amount":"base_payment_amount",
                "outstanding":"outstanding"
            }
        },
            "Purchase Taxes and Charges": {"doctype": "Purchase Taxes and Charges", "add_if_empty": True},
        },
        target_doc,
        set_missing_values,
    )

    return doc


# @frappe.whitelist()
# def make_delivery_note(source_name, target_doc=None, skip_item_mapping=False):
# 	from erpnext.stock.doctype.packed_item.packed_item import make_packing_list

# 	def set_missing_values(source, target):
# 		target.run_method("set_missing_values")
# 		target.run_method("set_po_nos")
# 		target.run_method("calculate_taxes_and_totals")

# 		if source.company_address:
# 			target.update({"company_address": source.company_address})
# 		else:
# 			# set company address
# 			target.update(get_company_address(target.company))

# 		if target.company_address:
# 			target.update(get_fetch_values("Delivery Note", "company_address", target.company_address))

# 		make_packing_list(target)

# 	def update_item(source, target, source_parent):
# 		target.base_amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.base_rate)
# 		target.amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.rate)
# 		target.qty = flt(source.qty) - flt(source.delivered_qty)

# 		item = get_item_defaults(target.item_code, source_parent.company)
# 		item_group = get_item_group_defaults(target.item_code, source_parent.company)

# 		if item:
# 			target.cost_center = (
# 				frappe.db.get_value("Project", source_parent.project, "cost_center")
# 				or item.get("buying_cost_center")
# 				or item_group.get("buying_cost_center")
# 			)

# 	mapper = {
# 		"Sales Order": {"doctype": "Delivery Note", "validation": {"docstatus": ["=", 1]}},
# 		"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
# 		"Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
# 	}

# 	if not skip_item_mapping:

# 		def condition(doc):
# 			# make_mapped_doc sets js `args` into `frappe.flags.args`
# 			if frappe.flags.args and frappe.flags.args.delivery_dates:
# 				if cstr(doc.delivery_date) not in frappe.flags.args.delivery_dates:
# 					return False
# 			return abs(doc.delivered_qty) < abs(doc.qty) and doc.delivered_by_supplier != 1

# 		mapper["Sales Order Item"] = {
# 			"doctype": "Delivery Note Item",
# 			"field_map": {
# 				"rate": "rate",
# 				"name": "so_detail",
# 				"parent": "against_sales_order",
# 			},
# 			"postprocess": update_item,
# 			"condition": condition,
            
# 		}

# 	target_doc = get_mapped_doc("Sales Order", source_name, mapper, target_doc, set_missing_values)

# 	return target_doc
# email templates
