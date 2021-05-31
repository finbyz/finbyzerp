import frappe

@frappe.whitelist()
def before_install():
	""" Function to set docperm for Local Admin """
	if not frappe.db.exists("Role", "Local Admin"):
		role_doc = frappe.new_doc("Role")
		role_doc.role_name = "Local Admin"
		role_doc.desk_access = 1
		role_doc.save()
		frappe.db.commit()
	
	count = frappe.db.sql("select count(*) from tabDocPerm where idx = 2 and role = 'Local Admin' And parent = 'Custom DocPerm'")
	if not count[0][0]:
		doc = frappe.new_doc("DocPerm")
		doc.read = 1
		doc.write = 1
		doc.create = 1
		doc.delete = 1
		doc.idx = 2
		doc.parent = "Custom DocPerm" #"Role"
		doc.role = "Local Admin"
		doc.parentfield = 'permissions'
		doc.parenttype = "DocType"

		doc.db_insert()
	
	count = frappe.db.sql("select count(*) from tabDocPerm where idx = 2 and role = 'Local Admin' And parent = 'Role'")
	if not count[0][0]:
		doc1 = frappe.new_doc("DocPerm")
		doc1.read = 1
		doc1.write = 1
		doc1.create = 1
		doc1.delete = 1
		doc1.idx = 2
		doc1.parent = "Role"
		doc1.role = "Local Admin"
		doc1.parentfield = 'permissions'
		doc1.parenttype = "DocType"
		
		doc1.db_insert()
	
	frappe.db.commit()

@frappe.whitelist()
def after_install():
	if not frappe.db.exists("Print Style", "FinByz"):
		print_style = frappe.new_doc("Print Style")
		print_style.print_style_name = 'FinByz'
		print_style.css = """
				.print-format * {
				color: #000 !important;
			}

			.print-format .alert {
				background-color: inherit;
				border: 1px dashed #333;
			}

			.print-format .table-bordered,
			.print-format .table-bordered > thead > tr > th,
			.print-format .table-bordered > tbody > tr > th,
			.print-format .table-bordered > tfoot > tr > th,
			.print-format .table-bordered > thead > tr > td,
			.print-format .table-bordered > tbody > tr > td,
			.print-format .table-bordered > tfoot > tr > td {
				border: 1px solid #333;
				margin: 0 !important;
					border-spacing: 0 !important;
			}
			.print-format .table-bordered > thead > tr > th{
			margin_bottom: 10px;
			}
			.tbspace > tbody > tr > td{
				padding: 0 5px 0 7px!important; margin:0!important; border-spacing: 0!important;
			}

			.print-format hr {
				border-top: 1px solid #333;
			}

			.print-heading {
				border-bottom: 2px solid #333;
			}
			@media screen {
					.print-format {
					background-color: white;
					box-shadow: 0px 0px 9px rgba(0,0,0,0.5);
					max-width: 8.3in;
					min-height: 11.69in;
					padding: 12px!important;
					margin: 12px!important;
					}
				}
			@media print {
				.print-format  {
					padding: 7px!important;
					margin: 7px!important;
				}
			}
		"""
		print_style.save()
		frappe.db.commit()

	print_setting = frappe.get_doc("Print Settings","Print Settings")
	print_setting.db_set('print_style','FinByz')
	frappe.db.commit()