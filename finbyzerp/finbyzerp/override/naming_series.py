import frappe
from frappe import _
from frappe.permissions import get_doctypes_with_read
from frappe.model.naming import parse_naming_series

@frappe.whitelist()
def get_transactions(self, arg=None):
	doctypes = list(set(frappe.db.sql_list("""select parent
			from `tabDocField` df where fieldname='naming_series'""")
		+ frappe.db.sql_list("""select dt from `tabCustom Field`
			where fieldname='naming_series'""")))

	doctypes = list(set(get_doctypes_with_read()).intersection(set(doctypes)))
	prefixes = ""
	for d in doctypes:
		options = ""
		try:
			options = self.get_options(d)
		except frappe.DoesNotExistError:
			frappe.msgprint(_('Unable to find DocType {0}').format(d))
			#frappe.pass_does_not_exist_error()
			continue
			
		#finbyz
		if options:
			options = get_naming_series_options(d)
			prefixes = prefixes + "\n" + options
	prefixes.replace("\n\n", "\n")
	prefixes = sorted(list(set(prefixes.split("\n"))))

	custom_prefixes = frappe.get_all('DocType', fields=["autoname"],
		filters={"name": ('not in', doctypes), "autoname":('like', '%.#%'), 'module': ('not in', ['Core'])})
	if custom_prefixes:
		prefixes = prefixes + [d.autoname.rsplit('.', 1)[0] for d in custom_prefixes]

	prefixes = "\n".join(sorted(prefixes))

	return {
		"transactions": "\n".join([''] + sorted(doctypes)),
		"prefixes": prefixes
	}

#finbyz
def get_naming_series_options(doctype):
	meta = frappe.get_meta(doctype)
	options = meta.get_field("naming_series").options.split("\n")	
	options_list = []

	fields = [d.fieldname for d in meta.fields]
	# frappe.msgprint(str(len(options)))

	for option in options:
		parts = option.split('.')

		if parts[-1] == "#" * len(parts[-1]):
			del parts[-1]

		naming_str = parse_naming_series(parts)
		series = {}
		dynamic_field = {}
		field_list = []
		
		for part in parts:
			if part in fields:
				field_list.append(part)
				dynamic_field[part] = (frappe.db.sql_list("select distinct {field} from `tab{doctype}` where {field} is not NULL".format(field=part, doctype=doctype)))
	
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
		
	return "\n".join(options_list)