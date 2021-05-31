// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Sales Invoice", "refresh", function(frm) {
    display_qr(frm);
    create_custom_button(frm);
})
frappe.ui.form.on("Sales Order", "refresh", function(frm) {
    display_qr(frm);
    create_custom_button(frm);
})
frappe.ui.form.on("Delivery Note", "refresh", function(frm) {
    display_qr(frm);
    create_custom_button(frm);
})
frappe.ui.form.on("Purchase Order", "refresh", function(frm) {
    display_qr(frm);
    create_custom_button(frm);
})
frappe.ui.form.on("Payment Entry", "refresh", function(frm) {
    display_qr(frm);
    create_custom_button(frm);
})
frappe.ui.form.on("Quotation", "refresh", function(frm) {
    display_qr(frm);
    create_custom_button(frm);
})


function display_qr(frm){
    let event = String(frappe.session.user + frm.doc.doctype + frm.doc.name)
    frappe.realtime.on(event, function(data) {
        var d = frappe.msgprint({
            title: __('Scan below QR Code in Whatsapp Web'),
            message: data,
            // "<img src='/private/files/'"+frappe.session.user + "'.png' alt='No Image'>",
            primary_action:{
                action(values) {
                    d.hide()
                }
            }
        });    
        setTimeout(function(){$(".modal.fade.in").modal('hide');},9000)    
    })
};

function create_custom_button(frm){
    frappe.call({
        method:"finbyzerp.whatsapp_manager.get_whatsapp_settings",
        args:{},
        callback: function(r){
            if (r.message ==true){
                    frm.page.add_menu_item(__('Send WhatsApp'), function() { 
                        whatsapp_dialog(frm);
                    });
            }
        }
        
    })
};

function check_whatsapp_login(frm){
    frappe.call({
        method:"finbyzerp.whatsapp_manager.whatsapp_login_check",
        args:{
            
        },
        freeze:true,
        freeze_message:__("<b><p style='font-size:50px'>Please Wait ....</p></b>"),
        callback: function(r){

        }
    })
};

function whatsapp_dialog(frm){
    var d = new frappe.ui.Dialog({
        title: 'Send Whatsapp',
        no_submit_on_enter: true,
        width: 400,
        fields: [
            {label:'Mobile Number', fieldtype:'Data', fieldname:'number', reqd:1,default:frm.doc.contact_mobile},
			{
				label:__("Message"),
				fieldtype:"Small Text",
				fieldname:"content",
			},
			{fieldtype: "Section Break"},
			{fieldtype: "Column Break"},
			{label:"Attach Document Print", fieldtype:"Check",
            fieldname:"attach_document_print"},
			{label:"Select Print Format", fieldtype:"Select",
            fieldname:"select_print_format"},
			{fieldtype: "Column Break"},
			{label:"Select Attachments", fieldtype:"HTML",
            fieldname:"select_attachments"},
            {fieldtype: "Section Break"},
            {label:'',fieldtype:'Read Only',default:" Note : Please ensure that Internet Connection is available on your Whatsapp device."},
        ],
        primary_action_label: 'Send',
        primary_action(values) {
                var v = d.get_values();
                var selected_attachments =
                    $.map($(d.wrapper).find("[data-file-name]:checked"), function (element) {
                        return $(element).attr("data-file-name");
                });
                frappe.show_alert({message:__("Sending Whatsapp..."), indicator:'green'})
                frappe.call({
                    method:"finbyzerp.whatsapp_manager.get_pdf_whatsapp",
                    args:{
                        doctype: frm.doc.doctype,
                        name:frm.doc.name,
                        attach_document_print:v.attach_document_print,
                        print_format:v.select_print_format,
                        selected_attachments:selected_attachments,
                        mobile_number:v.number,
                        description:v.content || ''
                    },
                    // freeze:true,
                    // freeze_message:__("<b><p style='font-size:35px'>Please Wait, File Sending is in Progress!!</p></b>"),
                    callback: function(r){
                        // setTimeout(function(){$(".modal.fade.in").modal('hide');},8000)
                    }
                })
                d.hide()
    }
    });
    // d.fields_dict.send.$input.addClass("btn-primary");
    // $("<div style='height:5px;'>").appendTo(d.fields_dict.send.$input)
    // $("<div style='width:50px;'>").appendTo(d.fields_dict.send.$input)
    // $("<div style='font-size:30px;'>").appendTo(d.fields_dict.send.$input)
    setup_print_language(d,frm);
    setup_print(d,frm);
    setup_attach(d,frm);
    d.show();


};

function selected_format(d,frm) {
    return d.fields_dict.select_print_format.input.value || (frm && frm.meta.default_print_format) || "Standard";
};

function get_print_format(d,frm,format) {
    if (!format) {
        format = selected_format(d,frm);
    }

    if (locals["Print Format"] && locals["Print Format"][format]) {
        return locals["Print Format"][format];
    } else {
        return {};
    }
};

function setup_print_language(d,frm) {
    var doc = frm.doc;
    var fields = d.fields_dict;

    //Load default print language from doctype
    frm.lang_code = doc.language

    if (get_print_format(d,frm).default_print_language) {
        var default_print_language_code = get_print_format(d,frm).default_print_language;
        frm.lang_code = default_print_language_code;
    }
};


function setup_print(d,frm) {
    // print formats
    var fields = d.fields_dict;

    // toggle print format
    $(fields.attach_document_print.input).click(function() {
        $(fields.select_print_format.wrapper).toggle($(d).prop("checked"));
    });

    // select print format
    $(fields.select_print_format.wrapper).toggle(false);

    if (frm) {
        $(fields.select_print_format.input)
            .empty()
            .add_options(frm.print_preview.print_formats)
            .val(frm.print_preview.print_formats[0]);
    } else {
        $(fields.attach_document_print.wrapper).toggle(false);
    }

};

function setup_attach(d,frm) {
    var fields = d.fields_dict;
    var attach = $(fields.select_attachments.wrapper);

    if (!frm.attachments) {
        frm.attachments = [];
    }

    let args = {
        folder: 'Home/Attachments',
        on_success: attachment => {
            frm.attachments.push(attachment);
            render_attachment_rows(d,attachment, frm);
        }
    };

    if (frm) {
        args = {
            doctype: frm.doctype,
            docname: frm.docname,
            folder: 'Home/Attachments',
            on_success: attachment => {
                frm.attachments.attachment_uploaded(attachment);
                render_attachment_rows(d,attachment, frm);
            }
        };
    }

    $(`
        <h6 class='text-muted add-attachment' style='margin-top: 12px; cursor:pointer;'>
            ${__("Select Attachments")}
        </h6>
        <div class='attach-list'></div>
        <p class='add-more-attachments'>
            <a class='text-muted small'>
                <i class='octicon octicon-plus' style='font-size: 12px'></i>
                ${__("Add Attachment")}
            </a>
        </p>
    `).appendTo(attach.empty());

    attach
        .find(".add-more-attachments a")
        .on('click', () => new frappe.ui.FileUploader(args));
    //render_attachment_rows(d,frm);
};

function render_attachment_rows(d,attachment,frm) {
    const select_attachments = d.fields_dict.select_attachments;
    const attachment_rows = $(select_attachments.wrapper).find(".attach-list");
    if (attachment) {
        attachment_rows.append(get_attachment_row(attachment, true));
    } else {
        let files = [];
        if (frm.attachments && frm.attachments.length) {
            files = files.concat(frm.attachments);
        }
        if (frm) {
            files = files.concat(frm.get_files());
        }

        if (files.length) {
            $.each(files, (i, f) => {
                if (!f.file_name) return;
                if (!attachment_rows.find(`[data-file-name="${f.name}"]`).length) {
                    f.file_url = frappe.urllib.get_full_url(f.file_url);
                    attachment_rows.append(get_attachment_row(f));
                }
            });
        }
    }
};

function get_attachment_row(attachment, checked) {
    return $(`<p class="checkbox">
        <label>
            <span>
                <input
                    type="checkbox"
                    data-file-name="${attachment.name}"
                    ${checked ? 'checked': ''}>
                </input>
            </span>
            <span class="small">${attachment.file_name}</span>
            <a href="${attachment.file_url}" target="_blank" class="text-muted small">
            <i class="fa fa-share" style="vertical-align: middle; margin-left: 3px;"></i>
        </label>
    </p>`);
};