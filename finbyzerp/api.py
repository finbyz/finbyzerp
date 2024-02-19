import frappe
from frappe.utils import now_datetime
from erpnext.accounts.utils import get_fiscal_year
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.repost_item_valuation.repost_item_valuation import execute_repost_item_valuation


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

    doclist = get_mapped_doc(
        doctype,
        source_name,
        {
            doctype: {
                "doctype": ref_doctype,
                "field_map": {
                    "company_name": "organization",
                    "customer_name": "organization",
                    "contact_email": "email_id",
                    "contact_mobile": "mobile_no",
                },
                "field_no_map": ["naming_series", "lead", "customer", "opportunity"],
            }
        },
        target_doc,
        set_missing_values,
    )

    return doclist

@frappe.whitelist()
def repost_transaction_entries():
	execute_repost_item_valuation()