frappe.ui.form.on('Stock Entry', {
	refresh: (frm) => {
		if (frm.doc.__islocal){
		frm.set_df_property("company", "read_only", (!frm.doc.__islocal || frm.doc.amended_from) ? 1 : 0);
	
		};
		// uncomment below code for display valuation rate diff between current entry and ledger entry
		// below function will work only if s_warehouse is exists in item table.

		// if(frm.doc.docstatus == 1){
		// 	frm.add_custom_button(__("Rate Diff"), function(){
		// 		frappe.call({
		// 			method:"finbyzerp.finbyzerp.doc_events.stock_entry.check_rate_diff",
		// 			args:{
		// 				"doctype":frm.doc.doctype,
		// 				"docname":frm.doc.name
		// 			},
		// 			callback: function(r){
		// 				if (r.message){
		// 					frappe.msgprint({
		// 						title:"Items Rate Difference",
		// 						message: r.message,
		// 						wide : true})
		// 				}
		// 			}
		// 		})
		// 	})
		// }
	},
	onload: (frm) => {
		if (frm.doc.__islocal){
			if (frm.doc.company){
				frappe.call({
					method: 'frappe.client.get_value',
					args: {
					  doctype: 'Company',
					  filters: {
						'name': frm.doc.company,
					  },
					  fieldname: ['company_series']
					},
					callback: function (r) {
						if (r.message.company_series){
						frm.set_value('company_series',r.message.company_series)
						}
					}
			})
			frm.trigger('change_series_value');
			}
		}
	},
	change_series_value: function (frm) {
		if (frappe.meta.get_docfield("Stock Entry", "series_value", frm.doc.name)){
			if (frm.doc.__islocal && frm.doc.company && !frm.doc.amended_from) {
				frappe.call({
					method: "finbyzerp.api.check_counter_series",
					args: {
						'name': frm.doc.naming_series,
						'date': frm.doc.posting_date,
						'company_series': frm.doc.company_series || null,
					},
					callback: function (e) {
						// frm.doc.series_value = e.message;
						frm.set_value('series_value', e.message);
					}
				});
				// frm.refresh_field('series_value')
			}
		}
	},
	naming_series: function (frm) {
		frm.trigger('change_series_value');
	},
	company: function (frm) {
		frm.trigger('change_series_value');
	},
	posting_date: function (frm) {
		frm.trigger('change_series_value');
	},
	qty_as_per_bom: function(frm){
		if(frm.doc.bom_no && frm.doc.work_order){
			let values = {'doc': cur_frm.doc, 'bom': frm.doc.bom_no, 'qty': frm.doc.fg_completed_qty};
			if(!values) return;
			values["company"] = frm.doc.company;
			frappe.call({
				method: "finbyzerp.finbyzerp.doc_events.stock_entry.qty_as_per_bom",
				args: values,
				freeze: true,
				callback: function(r) {
					if (!r.message) {
						frappe.throw(__("BOM does not contain any stock item"));
					} else {
						cur_frm.doc.items = []
						$.each(r.message, function(i, item) {
							let warehouse = null;
							if(!item.is_finished_item){
								warehouse = frm.doc.from_warehouse || item.source_warehouse || item.default_warehouse;
							}
							else{
								warehouse = frm.doc.to_warehouse || item.to_warehouse;
							}
							let d = frappe.model.add_child(cur_frm.doc, "Stock Entry Detail", "items");
							d.item_code = item.item_code;
							d.item_name = item.item_name;
							d.item_group = item.item_group;
							d.s_warehouse = item.is_finished_item ? null :warehouse;
							d.t_warehouse = item.is_finished_item ? warehouse :null;
							d.uom = item.stock_uom;
							d.stock_uom = item.stock_uom;
							d.conversion_factor = item.conversion_factor ? item.conversion_factor : 1;
							d.qty = item.qty;
							d.expense_account = item.expense_account;
							d.project = item.project;
							d.is_finished_item = item.is_finished_item;
							d.allow_zero_valuation_rate = 0;
							frm.events.set_basic_rate(frm, d.doctype, d.name);
						});
					}
					refresh_field("items");
				}
			});
		}
	},
	set_basic_rate: function(frm, cdt, cdn) {
		const item = locals[cdt][cdn];
		item.transfer_qty = flt(item.qty) * flt(item.conversion_factor);

		const args = {
			'item_code'			: item.item_code,
			'posting_date'		: frm.doc.posting_date,
			'posting_time'		: frm.doc.posting_time,
			'warehouse'			: cstr(item.s_warehouse) || cstr(item.t_warehouse),
			'serial_no'			: item.serial_no,
			'company'			: frm.doc.company,
			'qty'				: item.s_warehouse ? -1*flt(item.transfer_qty) : flt(item.transfer_qty),
			'voucher_type'		: frm.doc.doctype,
			'voucher_no'		: item.name,
			'allow_zero_valuation': 1,
		};

		if (item.item_code || item.serial_no) {
			frappe.call({
				method: "erpnext.stock.utils.get_incoming_rate",
				args: {
					args: args
				},
				callback: function(r) {
					frappe.model.set_value(cdt, cdn, 'basic_rate', (r.message || 0.0));
					frm.events.calculate_basic_amount(frm, item);
				}
			});
		}
	},
});