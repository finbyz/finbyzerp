# Copyright (c) 2023, Finbyz Tech. Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe import _
import frappe

def execute(filters=None):
    columns, data = [], []
    data = get_data(filters)
    columns = get_columns()

    return columns, data


def get_data(filters):
    user_dict = {}
    user_data = frappe.db.sql(
        """
		SELECT 
			name, full_name
		FROM
			`tabUser`
	""",
        as_dict=1,
    )

    for row in user_data:
        user_dict.update({row.name: row.full_name})

    condition = ""

    if filters.get("company"):
        condition += f""" and gl.company = '{filters.get("company")}'"""
    if filters.get("fiscal_year"):
        condition += f""" and gl.fiscal_year = '{filters.get("fiscal_year")}'"""

    data = frappe.db.sql(
        f""" Select gl.posting_date , gl.voucher_no , gl.voucher_type , gl.is_cancelled
							From `tabGL Entry` as gl Where gl.docstatus = 1 and gl.is_cancelled = 1 {condition}
							group by gl.voucher_no """,
        as_dict=1,
    )
    voucher_wise_dict = {}
    for row in data:
        if voucher_wise_dict.get(row.voucher_type):
            voucher_wise_dict[row.voucher_type].append(row.voucher_no)
        else:
            voucher_wise_dict[row.voucher_type] = [row.voucher_no]

    voucher_dict = {}
    amended_dict = {}
    for voucher in voucher_wise_dict:
        if not voucher_wise_dict[voucher]:
            return
        voucher_list = ", ".join(f"'{i}'" for i in voucher_wise_dict[voucher])
        voucher_data = frappe.db.sql(
            f"""
			SELECT
				name, owner, modified_by
			FROM 
				`tab{voucher}`
			WHERE
				name in ({voucher_list})
		""",
            as_dict=1,
        )

        postng_date = "posting_date"
        if voucher == "Asset":
            postng_date = "available_for_use_date"

        voucher_data += frappe.db.sql(
            f"""
			SELECT
				name, {postng_date} as posting_date, amended_from, owner, modified_by
			FROM 
				`tab{voucher}`
			WHERE
				amended_from in ({voucher_list})
		""",
            as_dict=1,
        )

        for row in voucher_data:
            if row.get("amended_from"):
                amended_dict[row.get("amended_from")] = {
                    "name": row.name,
                    "owner": row.owner,
                    "modifier": row.modified_by,
                    "posting_date": row.posting_date,
                }
            else:
                voucher_dict[row.name] = {
                    "owner": row.owner,
                    "modifier": row.modified_by,
                }

    for row in data:
        if voucher_dict.get(row.voucher_no):
            row.update(
                {
                    "created_by": user_dict[voucher_dict[row.voucher_no]["owner"]],
                    "last_modified_by": user_dict[
                        voucher_dict[row.voucher_no]["modifier"]
                    ],
                }
            )
        if amended_dict.get(row.voucher_no):
            row.update(
                {
                    "ameded_voucher": amended_dict[row.voucher_no]["name"],
                    "ameded_voucher_date": amended_dict[row.voucher_no]["posting_date"],
                    "ameded_created_by": user_dict[
                        amended_dict[row.voucher_no]["owner"]
                    ],
                    "ameded_last_modified_by": user_dict[
                        voucher_dict[row.voucher_no]["modifier"]
                    ],
                }
            )

    return data


def get_columns():
    return [
        {
            "label": _("Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {"label": _("Voucher Type"), "fieldname": "voucher_type", "width": 150},
        {
            "label": _("Voucher No"),
            "fieldname": "voucher_no",
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 180,
        },
        {
            "label": _("Created By"),
            "fieldname": "created_by",
            "fieldtype": "Data",
            "options": "User",
            "width": 170,
        },
        {
            "label": _("Last Modified By"),
            "fieldname": "last_modified_by",
            "fieldtype": "Data",
            "width": 170,
        },
        {
            "label": _("Ameded Voucher No"),
            "fieldname": "ameded_voucher",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Ameded Posting Date"),
            "fieldname": "ameded_voucher_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Ameded Created By"),
            "fieldname": "ameded_created_by",
            "fieldtype": "Data",
            "width": 170,
        },
        {
            "label": _("Ameded Modified By"),
            "fieldname": "ameded_last_modified_by",
            "fieldtype": "Data",
            "width": 170,
        },
    ]
