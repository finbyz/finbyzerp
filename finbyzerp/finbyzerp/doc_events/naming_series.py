import frappe
from finbyzerp.api import get_naming_series_name, get_fiscal
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils import cint, getdate


def before_naming(self, method):
    if not self.get("amended_from") and not self.get("name"):
        date = (
            self.get("transaction_date")
            or self.get("manufacturing_date")
            or self.get("date")
            or self.get("posting_date")
            or getdate()
        )

        try:
            fiscal = get_fiscal(date)
            # get fiscal year from fiscal year
            fiscal_year = get_fiscal_year(date)[0]
            self.fiscal_year = fiscal_year
            self.fiscal = fiscal
        except Exception:
            pass

        if not self.get("company_series"):
            self.company_series = None

        if self.get("series_value"):
            if self.series_value > 0:
                name = get_naming_series_name(
                    self.naming_series, fiscal, self.company_series
                )
                check = frappe.db.get_value("Series", name, "current", order_by="name")
                if check == 0:
                    pass
                elif not check:
                    frappe.db.sql(
                        f"INSERT INTO `tabSeries` (name, current) VALUES ('{name}', 0)"
                    )

                frappe.db.sql(
                    f"UPDATE `tabSeries` SET current = {cint(self.series_value) - 1} WHERE name = '{name}'"
                )

