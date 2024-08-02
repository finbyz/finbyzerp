
import frappe
from frappe.utils import now
def po_so_before_cancel(self,method):
    frappe.db.sql("""update `tabGL Entry`
        set against_voucher_type=null, against_voucher=null,
        modified=%s, modified_by=%s
        where against_voucher_type=%s and against_voucher=%s
        and voucher_no != ifnull(against_voucher, '') and is_cancelled = 1""",
        (now(), frappe.session.user, self.doctype, self.name))
    # from frappe.model.dynamic_links import get_dynamic_link_map
    # from frappe.model.delete_doc import raise_link_exists_exception
    # doctypes_to_skip = ("Communication", "ToDo", "DocShare", "Email Unsubscribe", "Activity Log", "File",
    # 	"Version", "Document Follow", "Comment" , "View Log", "Tag Link", "Notification Log", "Email Queue")
    # doc = frappe.get_doc(self.doctype,self.name)
    # method = "Cancel"
    # for df in get_dynamic_link_map().get(doc.doctype, []):

    # 	ignore_linked_doctypes = doc.get('ignore_linked_doctypes') or []

    # 	if df.parent in doctypes_to_skip or (df.parent in ignore_linked_doctypes and method == 'Cancel'):
    # 		# don't check for communication and todo!
    # 		continue

    # 	meta = frappe.get_meta(df.parent)
    # 	if meta.issingle:
    # 		# dynamic link in single doc
    # 		refdoc = frappe.db.get_singles_dict(df.parent)
    # 		if (refdoc.get(df.options)==doc.doctype
    # 			and refdoc.get(df.fieldname)==doc.name
    # 			and ((method=="Delete" and refdoc.docstatus < 2)
    # 				or (method=="Cancel" and refdoc.docstatus==1))
    # 			):
    # 			# raise exception only if
    # 			# linked to an non-cancelled doc when deleting
    # 			# or linked to a submitted doc when cancelling
    # 			raise_link_exists_exception(doc, df.parent, df.parent)
    # 	else:
    # 		# dynamic link in table
    # 		df["table"] = ", `parent`, `parenttype`, `idx`" if meta.istable else ""
    # 		for refdoc in frappe.db.sql("""select `name`, `docstatus` {table} from `tab{parent}` where
    # 			{options}=%s and {fieldname}=%s""".format(**df), (doc.doctype, doc.name), as_dict=True):

    # 			if ((method=="Delete" and refdoc.docstatus < 2) or (method=="Cancel" and refdoc.docstatus==1)):
    # 				# raise exception only if
    # 				# linked to an non-cancelled doc when deleting
    # 				# or linked to a submitted doc when cancelling

    # 				reference_doctype = refdoc.parenttype if meta.istable else df.parent
    # 				reference_docname = refdoc.parent if meta.istable else refdoc.name
    # 				at_position = "at Row: {0}".format(refdoc.idx) if meta.istable else ""
    # 				if reference_doctype in ["GL Entry","Stock Ledger Entry"]:
    # 					if frappe.db.exists(reference_doctype,{"name":reference_docname,"voucher_no":("!=",doc.name)}):
    # 						voucher_type,voucher_no = frappe.db.get_value(reference_doctype,{"name":reference_docname,"voucher_no":("!=",doc.name)},['voucher_type','voucher_no'])
    # 						if frappe.db.get_value(voucher_type,voucher_no,"docstatus") == 2:
    # 							frappe.db.sql("delete from `tabGL Entry` where voucher_type=%s and voucher_no=%s and is_cancelled = 1", (voucher_type, voucher_no))
    # 							frappe.db.sql("delete from `tabStock Ledger Entry` where voucher_type=%s and voucher_no=%s and is_cancelled = 1", (voucher_type, voucher_no))

    # 				# raise_link_exists_exception(doc, reference_doctype, reference_docname, at_position)
