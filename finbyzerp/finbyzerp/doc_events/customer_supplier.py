import frappe
from frappe import _


def before_rename(self, method, old, new, merge=False):
    account_type = "Supplier" if self.doctype == "Supplier" else "Payable"

    fiscal_year_frozen_till_date = frappe.db.get_value("Accounts Settings", None, "fiscal_year_frozen_till_date")
    if fiscal_year_frozen_till_date and merge:
        frappe.throw(
		    _(f"No one Authorized to Merge {account_type} as Fiscal Year Frozen Date has Applied")
		)

def validate(self, method):
    set_party_account_based_on_currency(self)

def set_party_account_based_on_currency(self):
    if self.default_currency:
        if self.doctype == "Customer":
            account_type = "Receivable"
        else:
            account_type = "Payable"
        if not frappe.db.exists(
            "GL Entry", {"party_type": self.doctype, "party": self.name}
        ):
            company_currency_list = frappe.get_all(
                "Company", fields=["name", "default_currency"]
            )
            account_dict = {}
            if self.accounts:
                for d in company_currency_list:
                    if self.default_currency != d["default_currency"]:
                        for row in self.accounts:
                            if row.company == d["name"]:
                                if not frappe.db.exists(
                                    "Account",
                                    {
                                        "account_type": account_type,
                                        "freeze_account": "No",
                                        "account_currency": self.default_currency,
                                        "company": d["name"],
                                    },
                                ):
                                    frappe.msgprint(
                                        "Please create {0} account in {1} for company {2} then try to change currency again".format(
                                            account_type,
                                            self.default_currency,
                                            d["name"],
                                        )
                                    )
                                else:
                                    row.account = frappe.db.get_value(
                                        "Account",
                                        {
                                            "account_type": account_type,
                                            "freeze_account": "No",
                                            "account_currency": self.default_currency,
                                            "company": d["name"],
                                            "is_group": 0,
                                        },
                                        "name",
                                    )
                            else:
                                if not frappe.db.exists(
                                    "Account",
                                    {
                                        "account_type": account_type,
                                        "freeze_account": "No",
                                        "account_currency": self.default_currency,
                                        "company": d["name"],
                                    },
                                ):
                                    frappe.msgprint(
                                        "Please create {0} account in {1} for company {2} then try to change currency again".format(
                                            account_type,
                                            self.default_currency,
                                            d["name"],
                                        )
                                    )
                                else:
                                    account_dict.update(
                                        {
                                            "company": d["name"],
                                            "account": frappe.db.get_value(
                                                "Account",
                                                {
                                                    "account_type": account_type,
                                                    "freeze_account": "No",
                                                    "company": d["name"],
                                                    "account_currency": self.default_currency,
                                                },
                                            ),
                                        }
                                    )
                    # frappe.msgprint(str(account_dict))
                    if account_dict:
                        self.extend("accounts", [account_dict])
            else:
                for d in company_currency_list:
                    if self.default_currency != d["default_currency"]:
                        if frappe.db.exists(
                            "Account",
                            {
                                "account_type": account_type,
                                "freeze_account": "No",
                                "company": d["name"],
                                "account_currency": self.default_currency,
                            },
                        ):
                            self.append(
                                "accounts",
                                {
                                    "company": d["name"],
                                    "account": frappe.db.get_value(
                                        "Account",
                                        {
                                            "account_type": account_type,
                                            "freeze_account": "No",
                                            "company": d["name"],
                                            "account_currency": self.default_currency,
                                        },
                                    ),
                                },
                            )
                        else:
                            frappe.msgprint(
                                "Please create {0} account in {1} for company {2} then try to change currency again".format(
                                    account_type, self.default_currency, d["name"]
                                )
                            )