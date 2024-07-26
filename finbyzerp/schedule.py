import frappe
from frappe.utils.background_jobs import enqueue
from frappe.utils import cint,cstr, getdate, get_fullname, get_url_to_form,now_datetime,validate_email_address,now
@frappe.whitelist()
def sales_invoice_payment_remainder():
    frappe.enqueue(send_sales_invoice_mails, queue='long', timeout=5000, job_name='Payment Reminder Mails')
    return "Payment Reminder Mails Send"


@frappe.whitelist()
def send_sales_invoice_mails():
    account_settings = frappe.get_doc("Accounts Settings")

    if not account_settings.send_overdue_reminder:
        return

    data = frappe.get_all("Sales Invoice", filters={
            'status': ['in', ('Overdue')],
            'outstanding_amount':(">", 5000),
            'docstatus': 1,
            'is_opening': 'No',
        },
        order_by='posting_date',
        group_by= "customer,company",
        fields=["group_concat(name) as name", "customer", "company"]
    )
    email_template = frappe.get_doc("Email Template", "Payment Reminder")

    if account_settings.send_testing_overdue_mail:
        recipients = ",".join([row.email_id for row in account_settings.test_recipients_emails])
        
    for d in data:
        sender = frappe.db.get_value("Company",d.company,"send_from_overdue_email")
        
        if not sender:
            continue
        
        context = {"customer": d.customer, "company": d.company}
        context['sales_invoices'] = [frappe.get_doc("Sales Invoice", name) for name in d.name.split(",")]

        recipients_emails = ",".join([doc.email for doc in context['sales_invoices'] if doc.email and doc.email.replace(" ", "")])
        emails = ",".join(sorted(list(set(recipients_emails.split(",")))))
        
        if not account_settings.send_testing_overdue_mail:
            if not recipients_emails:
                continue
            recipients = emails
        else:
            context["emails"] = emails

        try:
            frappe.sendmail(
                recipients=recipients,
                sender=sender,
                subject=frappe.render_template(email_template.subject, context),
                message=frappe.render_template(email_template.response_html, context),
            )
        except Exception as e:
            frappe.log_error("Mail Sending Issue", frappe.get_traceback())
            print(frappe.get_traceback())



def daily_entry_summary_mail():
    if frappe.db.exists("Daily Entry Summary","DES-001"):
        doc = frappe.get_doc("Daily Entry Summary","DES-001")

        recipients = doc.recipient.split(",") if doc.recipient.find(",") != -1 else doc.recipient
        if doc.daily_entry_summary and validate_email_address(recipients):
            message = ""
            for dtype in doc.doctypes:
                body = ''
                total = 0

                table_data = """
                    <table class="table table-bordered " style="font-size:100%; float: left;  width:auto; margin:10px 10px 10px 0;">
                    <thead><tr><th colspan="2"><b><center>{dtype}</center></b></th></tr></thead>
                """.format(dtype=dtype.document_type)

                query = frappe.db.sql("select owner,count(name) as no_of_entries from `tab{dtype}` where docstatus=1 and CAST(creation AS DATE) = CURDATE() GROUP BY owner".format(dtype=dtype.document_type),as_dict=1)

                if query:
                    for data in query:
                        total += data.no_of_entries
                        user = get_fullname(data.owner)
                        body +="""<tr>
                                    <td><center>{user}</center></td> <td><center><b>{no_of_entries}</b></center></td>
                                </tr>
                        """.format(user = user,no_of_entries=data.no_of_entries)

                    body += """<tr>
                                <td><center><b>Total</h5></b><center></td> <td><center><b>{total}</h5></b><center></td>
                            </tr>
                    """.format(total=total)
                else:
                    body += """<tr><td><b><center>0</center></b></td></tr>"""

                table_data += """
                            <tbody>{body}</tbody>
                    </table>
                """.format(body=body)

                message += """&nbsp;{table_data}&nbsp;
                """.format(table_data=table_data)

            frappe.sendmail(recipients=recipients,
                reference_doctype='User', reference_name="Administrator",
                subject='Daily Entry Summary', message="""<div style="width:100%;">""" + message + """</div>""", now=True)

def daily_transaction_summary_mail():
    if frappe.db.exists("Daily Entry Summary","DES-001"):
        doc = frappe.get_doc("Daily Entry Summary","DES-001")
        recipients = doc.recipient.split(",") if doc.recipient.find(",") != -1 else doc.recipient

        if doc.daily_transaction_summary and validate_email_address(recipients):
            message = ""
            for dtype in doc.doctypes:
                query_col = body = thead = table_data = ''
                total = 0

                query_columns = frappe.db.sql("""select fieldname,label from `tabDocField` where parent='{}' and in_list_view=1 ORDER BY idx""".format(dtype.document_type),as_dict=1)
                thead += """<th><center>Name</center></th>"""

                query_col = "name,"
                for lview in query_columns:
                    query_col += "{col},".format(col=lview.fieldname)
                    thead += """<th><center>{col}</center></th>""".format(col=lview.label)

                query_columns = query_col[:-1]

                table_data = """<p><h4><b>{dtype}:</b></h4></p></br></br>
                    <table class="table table-bordered" style="width:auto;">
                    <thead><tr>{thead}</tr></thead>
                """.format(dtype=dtype.document_type,thead=thead)
                
                # select_date = 'transaction_date' if dtype.document_type in ['Purchase Order','Sales Order'] else 'posting_date'
                query = frappe.db.sql("""select {query_columns} from `tab{dtype}` where docstatus = 1 and CAST(creation AS DATE) = CURDATE()""".format(query_columns=query_columns,dtype=dtype.document_type),as_dict=1)
                
                if query:
                    for data in query:
                        body += "<tr>"
                        for key in query_columns.split(","):
                            if key == "name":
                                url = get_url_to_form(dtype.document_type, data['{key}'.format(key=key)])
                                body+= """<td><center><a href={}>{}</a></center></td>""".format(url,data['{key}'.format(key=key)])
                            else:
                                body += """<td><center>{}</center></td>
                            """.format(data['{key}'.format(key=key)])
                        body += "</tr>"

                table_data += """
                            <tbody>{body}</tbody>
                    </table>
                """.format(body=body)

                message += """<br>{table_data}</br>
                """.format(table_data=table_data)
            
            frappe.sendmail(recipients=recipients,
                reference_doctype='User', reference_name="Administrator",
                subject='Daily Transaction Summary', message=message, now=True)
