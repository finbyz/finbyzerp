import frappe
from india_compliance.gst_india.utils.e_invoice import EInvoiceData
from india_compliance.gst_india.api_classes.e_invoice import EInvoiceAPI
import json
import jwt
from india_compliance.gst_india.utils.e_invoice import log_e_invoice
import io
from pyqrcode import create as qrcreate
from india_compliance.gst_india.utils.e_waybill import log_and_process_e_waybill_generation
from india_compliance.exceptions import GSPServerError
from india_compliance.gst_india.utils import (
    handle_server_errors,
    load_doc,
    parse_datetime,
    send_updated_doc,
)
from frappe import _
import os

@frappe.whitelist()
def generate_e_invoice(docname, throw=True, force=False):
    doc = load_doc("Sales Invoice", docname, "submit")

    settings = frappe.get_cached_doc("GST Settings")

    try:
        if (
            not force
            and settings.enable_retry_einv_ewb_generation
            and settings.is_retry_einv_ewb_generation_pending
        ):
            raise GSPServerError

        data = EInvoiceData(doc).get_data()
        api = EInvoiceAPI(doc)
        result = api.generate_irn(data)

        # Handle Duplicate IRN
        if result.InfCd == "DUPIRN":
            response = api.get_e_invoice_by_irn(result.Desc.Irn)

            if signed_data := response.SignedInvoice:
                invoice_data = json.loads(
                    jwt.decode(signed_data, options={"verify_signature": False})["data"]
                )

                previous_invoice_amount = invoice_data.get("ValDtls").get("TotInvVal")
                current_invoice_amount = data.get("ValDtls").get("TotInvVal")

                if previous_invoice_amount != current_invoice_amount:
                    frappe.throw(
                        _(
                            "e-Invoice is already available against Invoice {0} with a Grand Total of Rs.{1}"
                            " Duplicate IRN requests are not considered by e-Invoice Portal."
                        ).format(
                            frappe.bold(invoice_data.get("DocDtls").get("No")),
                            frappe.bold(previous_invoice_amount),
                        )
                    )

            # Handle error 2283:
            # IRN details cannot be provided as it is generated more than 2 days ago
            result = result.Desc if response.error_code == "2283" else response

        # Handle Invalid GSTIN Error
        if result.error_code in ("3028", "3029"):
            gstin = data.get("BuyerDtls").get("Gstin")
            response = api.sync_gstin_info(gstin)

            if response.Status != "ACT":
                frappe.throw(_("GSTIN {0} status is not Active").format(gstin))

            result = api.generate_irn(data)

    except GSPServerError as e:
        handle_server_errors(settings, doc, "e-Invoice", e)
        return

    except frappe.ValidationError as e:
        doc.db_set({"einvoice_status": "Failed"})

        if throw:
            raise e

        frappe.clear_last_message()
        frappe.msgprint(
            _(
                "e-Invoice auto-generation failed with error:<br>{0}<br><br>"
                "Please rectify this issue and generate e-Invoice manually."
            ).format(str(e)),
            _("Warning"),
            indicator="yellow",
        )

        return

    except Exception as e:
        doc.db_set({"einvoice_status": "Failed"})
        raise e

    doc.db_set(
        {
            "irn": result.Irn,
            "einvoice_status": "Generated",
            # "signed_qr_code": result.SignedQRCode #finbyz changes
        }
    )

    invoice_data = None
    if result.SignedInvoice:
        decoded_invoice = json.loads(
            jwt.decode(result.SignedInvoice, options={"verify_signature": False})[
                "data"
            ]
        )
        invoice_data = frappe.as_json(decoded_invoice, indent=4)

    log_e_invoice(
        doc,
        {
            "irn": doc.irn,
            "sales_invoice": docname,
            "acknowledgement_number": result.AckNo,
            "acknowledged_on": parse_datetime(result.AckDt),
            "signed_invoice": result.SignedInvoice,
            "signed_qr_code": result.SignedQRCode,
            "invoice_data": invoice_data,
            "is_generated_in_sandbox_mode": api.sandbox_mode,
        },
    )

    # #finbyz changes
    # is_qrcode_file_attached = doc.qrcode_image and frappe.db.exists(
    #     "File",
    #     {
    #         "attached_to_doctype": doc.doctype,
    #         "attached_to_name": doc.name,
    #         "file_url": doc.qrcode_image,
    #         "attached_to_field": "qrcode_image",
    #     },
    # )

    # if not is_qrcode_file_attached:
    #     if doc.signed_qr_code:
    #         attach_qrcode_image(doc)
    
    # #finbyz changes end

    if result.EwbNo:
        log_and_process_e_waybill_generation(doc, result, with_irn=True)

    if not frappe.request:
        return

    frappe.msgprint(
        _("e-Invoice generated successfully"),
        indicator="green",
        alert=True,
    )

    return send_updated_doc(doc)


def attach_qrcode_image(doc):
    qrcode = doc.signed_qr_code
    qr_image = io.BytesIO()
    url = qrcreate(qrcode, error="L")
    url.png(qr_image, scale=2, quiet_zone=1)
    qrcode_file = create_qr_code_file(doc, qr_image.getvalue())
    doc.db_set({
        "qrcode_image" : qrcode_file.file_url
    })

def create_qr_code_file(doc, qr_image):
    doctype = doc.doctype
    docname = doc.name
    filename = "QRCode_{}.png".format(docname).replace(os.path.sep, "__")

    _file = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": filename,
            "attached_to_doctype": doctype,
            "attached_to_name": docname,
            "attached_to_field": "qrcode_image",
            "is_private": 0,
            "content": qr_image,
        }
    )
    _file.save()
    frappe.db.commit()
    return _file