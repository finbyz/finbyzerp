# Copyright (c) 2022, Finbyz Tech. Pvt. Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _, whitelist
from frappe.model.workflow import apply_workflow


def execute(filters=None):
    columns, data = [], []
    data = get_data(filters)
    columns = get_columns(filters)
    return columns, data

def get_data(filters):
    conditions = ''
    if filters.get("doctype"):
        conditions += f""" and wf.document_type= '{filters.get('doctype')}'"""

    data = frappe.db.sql(f"""
		SELECT 
			wt.state, wt.idx, wt.next_state, wt.action, wt.allowed,
			wf.document_type, wf.workflow_state_field, wf.name as workflow
		FROM
			`tabWorkflow Transition` as wt
			JOIN `tabWorkflow` as wf on wf.name = wt.parent
		WHERE
			1 = 1 {conditions}
		ORDER BY
			wt.idx desc
	""", as_dict=True)

    workflow_map, doc_state, last_state = {}, {}, {}

    for idx, row in enumerate(data):

        if row.allowed not in frappe.get_roles():
            continue

        if frappe.db.get_value("Workflow State", row.next_state, "style") == "Success" and row.document_type not in last_state.keys():
            last_state.update({row.document_type: row.next_state})
            doc_state.update({row.document_type: row.workflow_state_field})

        workflow_map.update({(row.document_type, row.state): row})

    final_data = []

    for key in last_state:
        doc_data = frappe.db.sql(f"""
			SELECT
				name as doc_name,'{key}' as doctype_name, {doc_state[key]} as current_state
			FROM
				`tab{key}`
			WHERE
				docstatus !=2 and {doc_state[key]} != '{last_state[key]}'
			ORDER BY
				{doc_state[key]} asc
		""", as_dict=True)

        for row in doc_data:
            if workflow_map.get((row.doctype_name, row.current_state)):
                row.update(workflow_map[(row.doctype_name, row.current_state)])

                row['print_doc'] = f"""<button style='margin-left:5px;border:none;color: #fff; background-color: #1581E1; padding: 3px 5px;border-radius: 5px;'
					target="_blank" doctype='{row['doctype_name']}' docname='{row['doc_name']}'
					onClick=document_print_view(this.getAttribute('doctype'),this.getAttribute('docname'))>Print Document</button>"""

                row['apply_next_state'] = f"""<button style='margin-left:5px;border:none;color: #fff; background-color: #1581E1; padding: 3px 5px;border-radius: 5px;'
					target="_blank" state='{row['action']}' doctype='{row['doctype_name']}' docname='{row['doc_name']}'
					onClick=apply_action(this.getAttribute('state'),this.getAttribute('doctype'),this.getAttribute('docname'))>{row['action']}</button>"""

                final_data.append(row)

    return final_data


def get_columns(filters):
    columns = [
        {"label": _("WorkFlow Name"), "fieldname": "workflow",
         "fieldtype": "Data", "width": 200},
        {"label": _("Doctype"), "fieldname": "doctype_name",
         "fieldtype": "Link", "options": "DocType", "width": 140},
        {"label": _("Docname"), "fieldname": "doc_name",
         "fieldtype": "Dynamic Link", "options": "doctype_name", "width": 180},
        {"label": _("Current State"), "fieldname": "current_state",
         "fieldtype": "Data", "width": 250},
        {"label": _("Next State"), "fieldname": "next_state",
         "fieldtype": "Data", "width": 250},
        {"label": _("Print Document"), "fieldname": "print_doc",
         "fieldtype": "button", "width": 140},
        {"label": _("Apply Next State"), "fieldname": "apply_next_state",
         "fieldtype": "button", "width": 110}
    ]
    return columns


@frappe.whitelist()
def apply_next_state(state, doctype, docname):
    doc = frappe.get_doc(doctype, docname)
    apply_workflow(doc, state)
