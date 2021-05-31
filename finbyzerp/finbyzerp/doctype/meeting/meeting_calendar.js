frappe.views.calendar["Meeting"] = {
	field_map: {
		"start": "meeting_from",
		"end": "meeting_to",
		"id": "name",
		"title": "organization"
	},
	gantt: true,
	get_events_method: "finbyz.finbyz.doctype.meeting.meeting.get_events"
};