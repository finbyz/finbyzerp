frappe.ui.form.on('Account',{
    refresh: function(frm){
        frm.add_custom_button(__("Calculate Interest"), function() {
            var d = new frappe.ui.Dialog({
                title: "Calculate Interest",
                no_submit_on_enter: true,
                width: 500,
                fields: [
                    {label:'From Date', fieldtype:'Date', fieldname:'from_date', reqd:1},
                    {label:'Interest Rate', fieldtype:'Percent', fieldname:'interest_rate', reqd:1},
                    {fieldtype: "Column Break"},
                    {label:'To Date', fieldtype:'Date', fieldname:'to_date', reqd:1},
                    {fieldtype: "Section Break",},
                    {label:'Calculate', fieldtype:'Button', fieldname:'calculate'},
                    {fieldtype: "Section Break"},
                    {label:'Total Days', fieldtype:'Int', fieldname:'total_days','read_only': 1,},
                    {fieldtype: "Column Break"},
                    {label:'Interest Amount', fieldtype:'Float', fieldname:'interest_amount','read_only': 1,},
                    {fieldtype: "Section Break"},
                    {
                        "label":'',
                        "allow_bulk_edit": 1,
                        "fieldtype":'Table',
                        "fieldname":'date_wise_balance',
                        "read_only": 1,
                        "fields":[
                            {
                                'label': 'Date',
                                'fieldtype': 'Date',
                                'fieldname': 'date',
                                'in_list_view': 1,
                                'read_only': 1,
                            },
                            {
                                'label': 'Balance',
                                'fieldtype': 'Float',
                                'fieldname': 'balance',
                                'in_list_view': 1,
                                'read_only': 1,
                            },
                            {
                                'label': 'Days',
                                'fieldtype': 'Int',
                                'fieldname': 'days',
                                'in_list_view': 1,
                                'read_only': 1,
                            },
                        ]
                    }
                ]
            })
            
            d.fields_dict.calculate.input.onclick = function() {
                // let hideTheButtonWrapper = $('*[data-fieldname="date_wise_balance"]');
                // hideTheButtonWrapper.find('.grid-add-row').hide();
                var val = d.get_values()
                if (val.to_date < val.from_date){
                    frappe.throw("To Date Cannot be Before From Date")
                }
                d.set_value('total_days',frappe.datetime.get_day_diff(val.to_date, val.from_date));
                // Get Opening Balance
                frappe.call({
                    method:"finbyzerp.finbyzerp.doc_events.account.get_gl_data",
                    args:{
                        from_date:val.from_date,
                        to_date:val.to_date,
                        company:frm.doc.company,
                        account:frm.doc.name
                    },
                    freeze:true,
                    callback: function(r){
                        d.fields_dict.date_wise_balance.grid.df.data = r.message
                        d.fields_dict.date_wise_balance.grid.refresh()
                        var interest_amount = 0.0
                        var val = d.get_values()
                        if (val.date_wise_balance){
                            val.date_wise_balance.forEach(function (row){
                                interest_amount += (row.balance * row.days * val.interest_rate / (val.total_days * 100))
                            })
                            d.set_value('interest_amount',interest_amount)
                        }
                        let btn = document.createElement('a');
                        btn.innerText = 'Download';
                        btn.className = 'grid-download btn btn-xs btn-default';
                        d.fields_dict.date_wise_balance.grid.wrapper.find('.grid-download').removeClass('hide').parent().append(btn);
                        btn.addEventListener("click", function(){
                            var data = [];
                            var docfields = ["date","balance","days"];
                            data.push(["date","balance","days"])
                            data.push([])
                            val.date_wise_balance.forEach(function (v){
                                var row = []
                                docfields.forEach(function(df){
                                    var value = v[df]
                                    row.push(value || "")
                                });
                                data.push(row)
                            })
                            
                            frappe.tools.downloadify(data, null, "Interest_Calculation");
                        });
                    }
                })
            }
            d.show({
                
            });
        }); 
    }
})