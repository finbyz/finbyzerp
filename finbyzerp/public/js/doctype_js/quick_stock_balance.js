frappe.ui.form.on('Quick Stock Balance', {
    onload: function(frm) {
           frm.set_value('date', frappe.datetime.nowdate());
       }
   })