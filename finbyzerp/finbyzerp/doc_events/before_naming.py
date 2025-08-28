import frappe
from erpnext.accounts.utils import get_fiscal_year, flt
import datetime
from frappe.utils import cint,cstr, getdate, get_fullname, get_url_to_form,now_datetime,validate_email_address,now
def get_fiscal(date):
    fy = get_fiscal_year(date)[0]
    fiscal = frappe.db.get_value("Fiscal Year", fy, 'fiscal')

    return fiscal if fiscal else fy.split("-")[0][2:] + fy.split("-")[1][2:]

def before_naming(self, method):
    if not self.get('amended_from') and not self.get('name'):
        date = self.get("transaction_date") or self.get("posting_date") or  self.get("manufacturing_date") or self.get('date') or getdate()
        try:
            fiscal = get_fiscal(date)
            # get fiscal year from fiscal year
            fiscal_year = get_fiscal_year(date)[0]
            self.fiscal_year = fiscal_year
            self.fiscal = fiscal
        except Exception:
            pass
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
