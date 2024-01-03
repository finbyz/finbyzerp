frappe.provide("finbyzerp")
finbyzerp.open_stock_ledger = {
	open_stock_ledger: function (item_code, warehouse) {
		frappe.route_options = {
			"company": frappe.query_report.get_filter_value('company'),
			"from_date": frappe.query_report.get_filter_value('from_date') || data.year_start_date,
			"to_date": frappe.query_report.get_filter_value('to_date') || data.to_date || data.year_end_date,
			"item_code": item_code || frappe.query_report.get_filter_value('item_code'),
			"warehouse": warehouse || frappe.query_report.get_filter_value('warehouse')
		};
		let route = window.location.href.split("/app")[0] + "/app/query-report/Stock%20Ledger?company=" + frappe.route_options.company + "&from_date=" + frappe.route_options.from_date + "&to_date=" + frappe.route_options.to_date + "&warehouse=" + frappe.route_options.warehouse + "&item_code=" + frappe.route_options.item_code
		window.open(route, '_blank')
	}
}