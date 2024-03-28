import frappe
from frappe.model.utils import is_virtual_doctype
from frappe.desk.form.load import get_document_email, get_tags, get_milestones, get_additional_timeline_content, run_onload, set_link_titles, _get_communications, add_comments, get_attachments, get_versions, get_assignments, get_view_logs, get_point_logs
import json
from frappe import _, _dict
from frappe.permissions import get_doc_permissions
from frappe.desk.form.document_follow import is_document_followed


@frappe.whitelist()
def getdoc(doctype, name, user=None):
	"""
	Loads a doclist for a given document. This method is called directly from the client.
	Requries "doctype", "name" as form variables.
	Will also call the "onload" method on the document.
	"""

	if not (doctype and name):
		raise Exception("doctype and name required!")

	if not name:
		name = doctype

	if not is_virtual_doctype(doctype) and not frappe.db.exists(doctype, name):
		return []

	doc = frappe.get_doc(doctype, name)
	run_onload(doc)

	if not doc.has_permission("read"):
		frappe.flags.error_message = _("Insufficient Permission for {0}").format(
			frappe.bold(doctype + " " + name)
		)
		raise frappe.PermissionError(("read", doctype, name))

	# ignores system setting (apply_perm_level_on_api_calls) unconditionally to maintain backward compatibility
	doc.apply_fieldlevel_read_permissions()

	# add file list
	doc.add_viewed()
	get_docinfo(doc)

	doc.add_seen()
	set_link_titles(doc)
	if frappe.response.docs is None:
		frappe.local.response = _dict({"docs": []})
	frappe.response.docs.append(doc)
	
@frappe.whitelist()
def get_docinfo(doc=None, doctype=None, name=None):
	from frappe.share import _get_users as get_docshares

	if not doc:
		doc = frappe.get_doc(doctype, name)
		if not doc.has_permission("read"):
			raise frappe.PermissionError

	all_communications = _get_communications(doc.doctype, doc.name, limit=21)
	automated_messages = [
		msg for msg in all_communications if msg["communication_type"] == "Automated Message"
	]
	communications_except_auto_messages = [
		msg for msg in all_communications if msg["communication_type"] != "Automated Message"
	]

	docinfo = frappe._dict(user_info={})

	add_comments(doc, docinfo)

	docinfo.update(
		{
			"doctype": doc.doctype,
			"name": doc.name,
			"attachments": get_attachments(doc.doctype, doc.name),
			"communications": communications_except_auto_messages,
			"automated_messages": automated_messages,
			"total_comments": len(json.loads(doc.get("_comments") or "[]")),
			"versions": get_versions(doc),
			"assignments": get_assignments(doc.doctype, doc.name),
			"permissions": get_doc_permissions(doc),
			"shared": get_docshares(doc),
			"views": get_view_logs(doc.doctype, doc.name),
			"energy_point_logs": get_point_logs(doc.doctype, doc.name),
			"additional_timeline_content": get_additional_timeline_content(doc.doctype, doc.name),
			"milestones": get_milestones(doc.doctype, doc.name),
			"is_document_followed": is_document_followed(doc.doctype, doc.name, frappe.session.user),
			"tags": get_tags(doc.doctype, doc.name),
			"document_email": get_document_email(doc.doctype, doc.name),
			"owner": doc.owner,
			"modified_by": doc.modified_by,
		}
	)

	update_user_info(docinfo)

	frappe.response["docinfo"] = docinfo

def update_user_info(docinfo):
	users = set()

	users.update(d.sender for d in docinfo.communications)
	users.update(d.user for d in docinfo.shared)
	users.update(d.owner for d in docinfo.assignments)
	users.update(d.owner for d in docinfo.views)
	users.update(d.owner for d in docinfo.workflow_logs)
	users.update(d.owner for d in docinfo.like_logs)
	users.update(d.owner for d in docinfo.info_logs)
	users.update(d.owner for d in docinfo.attachment_logs)
	users.update(d.owner for d in docinfo.assignment_logs)
	users.update(d.owner for d in docinfo.comments)
	users.update(d.owner for d in docinfo.versions)

	users.update({docinfo.owner})
	users.update({docinfo.modified_by})
	
	for user in users:
		frappe.utils.add_user_info(user, docinfo.user_info)
