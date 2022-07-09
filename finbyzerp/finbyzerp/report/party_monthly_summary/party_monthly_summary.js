// Copyright (c) 2016, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
};
frappe.query_reports["Party Monthly Summary"] = {
	onload: function() {
		var party = getUrlParameter("party");
		if(party){
			setTimeout(()=>{
				frappe.query_report.set_filter_value('party', party);
			},150)
		}
	},
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
		{
			"fieldname":"period",
			"label": __("Period"),
			"fieldtype": "Select",
			"options": [
				{ "value": "Monthly", "label": __("Monthly") },
				{ "value": "Quarterly", "label": __("Quarterly") },
				{ "value": "Half-Yearly", "label": __("Half-Yearly") },
				{ "value": "Yearly", "label": __("Yearly") }
			],
			"default": "Monthly"
		},
		{
			"fieldname":"party_type",
			"label": __("Party Type"),
			"fieldtype": "Link",
			"options": "Party Type",
			"reqd": 1,
			on_change: () => {
				frappe.query_report.set_filter_value('party', "");
			}
		},
		{
			"fieldname":"party",
			"label": __("Party"),
			"fieldtype": "Dynamic Link",
			"options": "party_type",
			"reqd": 1
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default":frappe.defaults.get_user_default("year_start_date"),
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
		},
		{
			"fieldname":"cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options":"Cost Center"
		},
	]
};
function open_general_ledger(company, from_date, to_date, party_type, party, cost_center){
	
	if (cost_center == "None"){
		window.open(window.location.href.split('app')[0] + "app/query-report/General Ledger" + "/?" + "company=" + company + "&" +  "from_date="+ from_date + "&" + "to_date=" +to_date + "&" +"party_type="+party_type + "&" +"party="+encodeURIComponent(party),"_blank")
	}
	else{
		window.open(window.location.href.split('app')[0] + "app/query-report/General Ledger" + "/?" + "company=" + company + "&" +  "from_date="+ from_date + "&" + "to_date=" +to_date + "&" +"party_type="+party_type + "&" +"party="+encodeURIComponent(party) + "&" +"cost_center="+cost_center,"_blank")	
	}
}