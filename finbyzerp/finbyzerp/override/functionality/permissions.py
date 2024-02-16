import frappe
from frappe import _
from frappe.permissions import (
    get_doc_name,
    get_doc_permissions,
    get_role_permissions,
    has_child_permission,
    print_has_permission_check_logs,
    push_perm_check_log,
    _debug_log
)
from frappe.utils import cint

@print_has_permission_check_logs
def has_permission(
    doctype,
    ptype="read",
    doc=None,
    user=None,
    raise_exception=True,
    *,
    parent_doctype=None,
    debug=False,
) -> bool:
    """Return True if user has permission `ptype` for given `doctype`.
    If `doc` is passed, also check user, share and owner permissions.

    :param doctype: DocType to check permission for
    :param ptype: Permission Type to check
    :param doc: Check User Permissions for specified document.
    :param user: User to check permission for. Defaults to current user.
    :param raise_exception:
            DOES NOT raise an exception.
            If not False, will display a message using frappe.msgprint
                    which explains why the permission check failed.

    :param parent_doctype:
            Required when checking permission for a child DocType (unless doc is specified)
    """

    if not user:
        user = frappe.session.user

    if user == "Administrator":
        debug and _debug_log("Allowed everything because user is Administrator")
        return True

    if ptype == "share" and frappe.get_system_settings("disable_document_sharing"):
        debug and _debug_log("User can't share because sharing is disabled globally from system settings")
        return False

    if not doc and hasattr(doctype, "doctype"):
        # first argument can be doc or doctype
        doc = doctype
        doctype = doc.doctype
    
    not_allowed_doctype = [
        "Customize Form",
        "Client Script",
        "Server Script",
        "DocType",
        "Custom Field",
    ]
        
    if doctype in not_allowed_doctype:
        debug and _debug_log(f"Not Allowed Doctype {not_allowed_doctype}")
        return False

    if frappe.is_table(doctype):
        return has_child_permission(doctype, ptype, doc, user, raise_exception, parent_doctype, debug=debug)

    meta = frappe.get_meta(doctype)

    if doc:
        if isinstance(doc, (str, int)):
            doc = frappe.get_doc(meta.name, doc)
        perm = get_doc_permissions(doc, user=user, ptype=ptype, debug=debug).get(ptype)
        if not perm:
            debug and _debug_log(
                "Permission check failed from role permission system. Check if user's role grant them permission to the document."
            )
            msg = _("User {0} does not have access to this document").format(frappe.bold(user))
            if frappe.has_permission(doc.doctype):
                msg += f": {_(doc.doctype)} - {doc.name}"
            push_perm_check_log(msg, debug=debug)
    else:
        if ptype == "submit" and not cint(meta.is_submittable):
            push_perm_check_log(_("Document Type is not submittable"), debug=debug)
            return False

        if ptype == "import" and not cint(meta.allow_import):
            push_perm_check_log(_("Document Type is not importable"), debug=debug)
            return False

        role_permissions = get_role_permissions(meta, user=user, debug=debug)
        debug and _debug_log(
            "User has following permissions using role permission system: "
            + frappe.as_json(role_permissions, indent=8)
        )

        perm = role_permissions.get(ptype)

        if not perm:
            push_perm_check_log(
                _("User {0} does not have doctype access via role permission for document {1}").format(
                    frappe.bold(user), frappe.bold(doctype)
                ),
                debug=debug,
            )

    def false_if_not_shared():
        if ptype not in ("read", "write", "share", "submit", "email", "print"):
            debug and _debug_log(f"Permission type {ptype} can not be shared")
            return False

        rights = ["read" if ptype in ("email", "print") else ptype]

        if doc:
            doc_name = get_doc_name(doc)
            shared = frappe.share.get_shared(
                doctype,
                user,
                rights=rights,
                filters=[["share_name", "=", doc_name]],
                limit=1,
            )
            debug and _debug_log(f"Document is shared with user for {ptype}? {bool(shared)}")
            return bool(shared)

        elif frappe.share.get_shared(doctype, user, rights=rights, limit=1):
            # if atleast one shared doc of that type, then return True
            # this is used in db_query to check if permission on DocType
            debug and _debug_log(f"At least one document is shared with user with perm: {rights}")
            return True

        return False

    if not perm:
        debug and _debug_log("Checking if document/doctype is explicitly shared with user")
        perm = false_if_not_shared()

    return bool(perm)
