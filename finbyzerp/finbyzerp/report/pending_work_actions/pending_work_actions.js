// Copyright (c) 2022, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Pending Work Actions"] = {
	"filters": [
		{
			"fieldname": "doctype",
			"label": __("DocType"),
			"fieldtype": "Link",
			"options": "DocType"
		}
	]
};
function document_print_view(doctype, docname){
	window.open(`/app/print/${doctype}/${encodeURIComponent(docname)}`,"_blank")
}

function apply_action(state, doctype, docname){
	frappe.call({
		method: "finbyzerp.finbyzerp.report.pending_work_actions.pending_work_actions.apply_next_state",
		args: {
			state: state,
			doctype: doctype,
			docname: docname
		},
		freeze:true,
		freeze_message: `Taking action for ${doctype} ${docname}`,
		callback: function(r) {
			frappe.msgprint(`Action is Applied for ${doctype} ${docname}`)
			frappe.query_report.refresh();
		}
	});
}