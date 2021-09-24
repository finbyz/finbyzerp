frappe.request.report_error = function(xhr, request_opts) {
	var data = JSON.parse(xhr.responseText);
	var exc;
	if (data.exc) {
		try {
			exc = (JSON.parse(data.exc) || []).join("\n");
		} catch (e) {
			exc = data.exc;
		}
		delete data.exc;
	} else {
		exc = "";
	}

	var show_communication = function() {
		var error_report_message = [
			'<h5>Please type some additional information that could help us reproduce this issue:</h5>',
			'<div style="min-height: 100px; border: 1px solid #bbb; \
				border-radius: 5px; padding: 15px; margin-bottom: 15px;"></div>',
			'<hr>',
			'<h5>App Versions</h5>',
			'<pre>' + JSON.stringify(frappe.boot.versions, null, "\t") + '</pre>',
			'<h5>Route</h5>',
			'<pre>' + frappe.get_route_str() + '</pre>',
			'<hr>',
			'<h5>Error Report</h5>',
			'<pre>' + exc + '</pre>',
			'<hr>',
			'<h5>Request Data</h5>',
			'<pre>' + JSON.stringify(request_opts, null, "\t") + '</pre>',
			'<hr>',
			'<h5>Response JSON</h5>',
			'<pre>' + JSON.stringify(data, null, '\t')+ '</pre>'
		].join("\n");

		var communication_composer = new frappe.views.CommunicationComposer({
			subject: 'Error Report [' + frappe.datetime.nowdate() + ']',
			recipients: error_report_email,
			txt: error_report_message,
			doc: {
				doctype: "User",
				name: frappe.session.user
			}
		});
		communication_composer.dialog.$wrapper.css("z-index", cint(frappe.msg_dialog.$wrapper.css("z-index")) + 1);
	}

	if (exc) {
		var error_report_email = frappe.boot.error_report_email;

		request_opts = frappe.request.cleanup_request_opts(request_opts);

		// window.msg_dialog = frappe.msgprint({message:error_message, indicator:'red', big: true});

		if (!frappe.error_dialog) {
			frappe.error_dialog = new frappe.ui.Dialog({
				title: __('Server Error'),
				primary_action_label: __('Report'),
				primary_action: () => {
					if (error_report_email) {
						show_communication();
					} else {
						frappe.msgprint(__('Support Email Address Not Specified'));
					}
					frappe.error_dialog.hide();
				}
			});
			frappe.error_dialog.wrapper.classList.add('msgprint-dialog');

		}

		let parts = strip(exc).split('\n');

		frappe.error_dialog.$body.html(parts[parts.length - 1]);
		frappe.error_dialog.show();

	}
};