import frappe


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
					padding: 0px!important;
					margin: 0px!important;
					}
				}
			@media print {
				.print-format  {
					padding: 0px!important;
					margin: 0px!important;
				}
			}
		"""
		print_style.save()
		frappe.db.commit()

	print_setting = frappe.get_doc("Print Settings","Print Settings")
	print_setting.db_set('print_style','FinByz')
	update_website_settings()
	frappe.db.commit()

def update_website_settings():
	doc = frappe.get_doc("Website Settings")
	doc.home_page = "login"
	doc.app_name = "FinbyzERP"
	doc.disable_signup = 1
	doc.hide_footer_signup = 1
	doc.banner_image="/assets/finbyzerp/images/favicon.ico"
	doc.splash_image="/assets/finbyzerp/images/FinbyzLogo.svg"
	doc.app_logo="/assets/finbyzerp/images/FinbyzLogo.svg"
	doc.favicon="/assets/finbyzerp/images/favicon.ico"
	doc.save(ignore_permissions=True)
	doc.save(ignore_permissions=True)
