import frappe
from frappe import _
from frappe.permissions import (
    get_doc_name,
    get_doc_permissions,
    get_role_permissions,
    has_child_permission,
    print_has_permission_check_logs,
    push_perm_check_log,
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
):
    """Returns True if user has permission `ptype` for given `doctype`.
    If `doc` is passed, it also checks user, share and owner permissions.

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
        return True

    if ptype == "share" and frappe.get_system_settings("disable_document_sharing"):
        return False

    if not doc and hasattr(doctype, "doctype"):
        # first argument can be doc or doctype
        doc = doctype
        doctype = doc.doctype

    if doctype in [
        "Customize Form",
        "Client Script",
        "Server Script",
        "DocType",
        "Custom Field",
    ]:
        return False

    if frappe.is_table(doctype):
        return has_child_permission(
            doctype, ptype, doc, user, raise_exception, parent_doctype
        )

    meta = frappe.get_meta(doctype)

    if doc:
        if isinstance(doc, (str, int)):
            doc = frappe.get_doc(meta.name, doc)
        perm = get_doc_permissions(doc, user=user, ptype=ptype).get(ptype)
        if not perm:
            msg = _("User {0} does not have access to this document").format(
                frappe.bold(user)
            )
            if frappe.has_permission(doc.doctype):
                msg += f": {_(doc.doctype)} - {doc.name}"
            push_perm_check_log(msg)
    else:
        if ptype == "submit" and not cint(meta.is_submittable):
            push_perm_check_log(_("Document Type is not submittable"))
            return False

        if ptype == "import" and not cint(meta.allow_import):
            push_perm_check_log(_("Document Type is not importable"))
            return False

        role_permissions = get_role_permissions(meta, user=user)
        perm = role_permissions.get(ptype)

        if not perm:
            push_perm_check_log(
                _(
                    "User {0} does not have doctype access via role permission for document {1}"
                ).format(frappe.bold(user), frappe.bold(doctype))
            )

    def false_if_not_shared():
        if ptype in ("read", "write", "share", "submit", "email", "print"):

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

                if shared:
                    if ptype in (
                        "read",
                        "write",
                        "share",
                        "submit",
                    ) or meta.permissions[0].get(ptype):
                        return True

            elif frappe.share.get_shared(doctype, user, rights=rights, limit=1):
                # if atleast one shared doc of that type, then return True
                # this is used in db_query to check if permission on DocType
                return True

        return False

    if not perm:
        perm = false_if_not_shared()

    return bool(perm)
