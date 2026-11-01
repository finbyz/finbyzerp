import frappe
from frappe.utils import flt
from frappe.utils import get_link_to_form


def validate(self, method):
    validate_source_and_target_warehoouse(self)


def after_insert(self, method):
    create_quality_inspection_entry(self)


def on_submit(self, method):
    check_quality_inspection_status(self)
    validate_additional_cost(self)


def validate_source_and_target_warehoouse(self):
    if self.purpose in ["Material Transfer", "Material Transfer for Manufacture"]:
        for row in self.items:
            if row.s_warehouse == row.t_warehouse:
                frappe.throw(
                    "Source and Target warehouse can not be same for materil transfer entry."
                )


def create_quality_inspection_entry(self):
    for inspection_item in self.items:
        item = frappe.get_doc("Item", inspection_item.item_code)
        if self.purpose == "Manufacture":
            if (
                item.inspection_required_after_stock_entry
                and inspection_item.is_finished_item
            ):
                if inspection_item.t_warehouse:
                    quality_inspection = frappe.new_doc("Quality Inspection")
                    quality_inspection.naming_series = "MAT-IS-.YYYY.-"
                    quality_inspection.item_code = inspection_item.item_code
                    quality_inspection.ref_itm = inspection_item.name
                    quality_inspection.inspection_type = "Outgoing"
                    quality_inspection.reference_type = "Stock Entry"
                    quality_inspection.reference_name = self.name
                    quality_inspection.sample_size = inspection_item.qty
                    quality_inspection.description = inspection_item.description
                    quality_inspection.remarks = self.remarks
                    quality_inspection.inspected_by = self.modified_by
                    quality_inspection.sample_size_uom = inspection_item.uom
                    quality_inspection.batch_no = inspection_item.batch_no
                    quality_inspection.quality_inspection_template = (
                        frappe.db.get_value(
                            "Item",
                            inspection_item.item_code,
                            "quality_inspection_template",
                        )
                    )
                    try:
                        quality_inspection.save(ignore_permissions=True)
                    except Exception as e:
                        frappe.throw(str(e))
                    else:
                        frappe.db.set_value(
                            inspection_item.doctype,
                            inspection_item.name,
                            "quality_inspection",
                            quality_inspection.name,
                        )
                        frappe.msgprint(
                            "Quality Inspection {} is Created".format(
                                get_link_to_form(
                                    "Quality Inspection", quality_inspection.name
                                )
                            )
                        )


def validate_additional_cost(self):
    if self.purpose in ["Repack", "Manufacture"]:
        diff = abs(
            round(flt(self.value_difference, 1))
            - (round(flt(self.total_additional_costs, 1)))
        )
        if diff > 5:
            frappe.throw(
                "ValuationError: Value difference between incoming and outgoing amount is higher than additional cost"
            )


def check_quality_inspection_status(self):
    doc = frappe.db.exists(
        "Quality Inspection", {"reference_name": self.name, "docstatus": 0}
    )
    if doc:
        qi_doc = frappe.get_doc("Quality Inspection", doc)
        if qi_doc.docstatus == 0:
            frappe.throw(
                "Quality Inspection Is Not Submited <br> Please Submit Quality Inspection {}".format(
                    get_link_to_form("Quality Inspection", doc)
                )
            )
