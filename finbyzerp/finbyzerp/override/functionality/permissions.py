import frappe
from frappe import _
from frappe.permissions import setup_custom_perms
from frappe.core.doctype.doctype.doctype import validate_permissions_for_doctype
from frappe.core.doctype.access_log.access_log import make_access_log
from frappe.utils.response import send_private_file
from werkzeug.exceptions import Forbidden


def add_permission(doctype, role, permlevel=0, ptype=None):
    """Add a new permission rule to the given doctype
    for the given Role and Permission Level"""

    setup_custom_perms(doctype)
    if frappe.db.get_value(
        "Custom DocPerm",
        dict(parent=doctype, role=role, permlevel=permlevel, if_owner=1),
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


def download_backup(path):
    try:
        frappe.only_for(("System Manager", "Administrator", "Local Admin"))
        make_access_log(report_name="Backup")
    except frappe.PermissionError:
        raise Forbidden(
            _(
                "You need to be logged in and have System Manager Role to be able to access backups."
            )
        )

    return send_private_file(path)
