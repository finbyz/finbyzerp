import frappe
from frappe.model.workflow import get_workflow_name, send_email_alert
from frappe.workflow.doctype.workflow_action.workflow_action import (
	clear_workflow_actions, get_next_possible_transitions, get_doc_workflow_state,
	is_workflow_action_already_created, update_completed_workflow_actions, get_users_next_action_data, get_common_email_args, deduplicate_actions)
from frappe.desk.notifications import clear_doctype_notifications
from frappe.workflow.doctype.workflow_action.workflow_action import create_workflow_actions_for_roles
from frappe.utils.background_jobs import enqueue
from frappe.desk.doctype.notification_log.notification_log import make_notification_logs


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