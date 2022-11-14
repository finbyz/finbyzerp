// Copyright (c) 2016, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Activity Analysis"] = {
    "filters": [{
            "fieldname": "based_on",
            "label": __("Based On"),
            "fieldtype": "Select",
            "options": ["Creation Date", "Posting Date"],
            "default": "Posting Date"
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
        },
        {
            "fieldname": "doctype",
            "label": __("DocType"),
            "fieldtype": "Select",
            "options": "\nQuotation\nPurchase Order\nPurchase Receipt\nPurchase Invoice\nSales Order\nDelivery Note\nSales Invoice\nStock Entry\nJournal Entry\nPayment Entry\nJob Card"
        },
        {
            "fieldname": "user",
            "label": __("User"),
            "fieldtype": "Link",
            "options": "User"
        },
        {
            "fieldname": "timespan",
            "label": __("Timespan"),
            "fieldtype": "Select",
            "width": "80",
            "options": "\nlast year\nlast 6 month\nlast quarter\nlast month\nlast week\nyesterday\ntoday\nthis week\nthis month\nthis quarter\nthis year",
            "default": "yesterday"
        },
        {
            "fieldname": "show_details",
            "label": __("Show Details"),
            "fieldtype": "Check",
            "default": 1
        },
        {
            "fieldname": "show_debit_credit_wise_amount",
            "label": __("Show Debit Credit wise Amount"),
            "fieldtype": "Check",
            "depends_on": "eval:doc.show_details == 1"
        },
    ]
};