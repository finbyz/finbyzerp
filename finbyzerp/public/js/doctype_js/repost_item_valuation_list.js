frappe.listview_settings['Repost Item Valuation'] = {
    onload(listview) {
        listview.page.add_menu_item(__("Schedule Repost Entries"), function () {
            frappe.call({
                method: 'finbyzerp.api.repost_transaction_entries',
                callback: function () {
                }
            });
        });
    },
}