import frappe
from frappe.core.doctype.document_naming_settings.document_naming_settings import (
    DocumentNamingSettings as _DocumentNamingSettings,
)
from frappe.model.naming import parse_naming_series


def get_naming_series_options(doctype):
    meta = frappe.get_meta(doctype)
    options_list = []
    if meta.get_field("naming_series").get("options"):
        options = meta.get_field("naming_series").options.split("\n")
        options_list = []

        fields = [d.fieldname for d in meta.fields]

        for option in options:
            parts = option.split(".")

            if parts[-1] == "#" * len(parts[-1]):
                del parts[-1]

            naming_str = parse_naming_series(parts)
            dynamic_field = {}
            field_list = []

            for part in parts:
                if part in fields:
                    field_list.append(part)
                    dynamic_field[part] = frappe.db.sql_list(
                        "select distinct {field} from `tab{doctype}` where {field} is not NULL".format(
                            field=part, doctype=doctype
                        )
                    )

            import itertools

            if dynamic_field.items():
                pair = [(k, v) for k, v in dynamic_field.items()]
                key = [item[0] for item in pair]
                value = [item[1] for item in pair]

                combination = list(itertools.product(*value))
                for item in combination:
                    name = naming_str
                    for k, v in zip(key, item):
                        name = name.replace(k, v)

                    options_list.append(name)

    return options_list


class DocumentNamingSettings(_DocumentNamingSettings):
    def _get_prefixes(self, doctypes) -> list[str]:
        """Get all prefixes for naming series.

        - For all templates prefix is evaluated considering today's date
        - All existing prefix in DB are shared as is.
        """
        series_templates = set()
        for d in doctypes:
            try:
                options = get_naming_series_options(d)
                series_templates.update(options)
            except frappe.DoesNotExistError:
                frappe.msgprint(_("Unable to find DocType {0}").format(d))
                continue

        custom_templates = frappe.get_all(
            "DocType",
            fields=["autoname"],
            filters={
                "name": ("not in", doctypes),
                "autoname": ("like", "%.#%"),
                "module": ("not in", ["Core"]),
            },
        )
        if custom_templates:
            series_templates.update(
                [d.autoname.rsplit(".", 1)[0] for d in custom_templates]
            )

        return self._evaluate_and_clean_templates(series_templates)
