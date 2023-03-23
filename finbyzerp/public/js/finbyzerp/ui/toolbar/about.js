frappe.provide('frappe.ui.misc');
frappe.ui.misc.about = function() {
	if(!frappe.ui.misc.about_dialog) {
		var d = new frappe.ui.Dialog({title: __('<img src="https://finbyz.tech/files/finbyz-tech.svg" width="180">')});

		$(d.body).html(repl("<div>\
		<p>"+__("At Finbyz Tech, we are passionate about revolutionizing businesses through the latest technology.")+"</p>  \
		<p><i class='fa fa-globe fa-fw'></i>\
			Website: <a href=' https://finbyz.tech' target='_blank'> https://finbyz.tech</a></p>\
		<p><i class='fa fa-youtube-play aria-hidden=true'></i>\
			Youtube Tutorial  : <a href=' https://www.youtube.com/@Finbyz'> https://www.youtube.com/@Finbyz</a></p>\
		<p><i class='fa fa-solid fa-envelope fa-fw'></i>\
			Support: <a href='support@finbyz.tech' target='_blank'>support@finbyz.tech</a></p>\
		<p><i class='fa fa-phone fa-fw'></i>\
			Phone:<a href='tel:079 48912428'> 079 48912428</a></p>\
		<hr>\
		<h4>Installed Apps</h4>\
		<div id='about-app-versions'>Loading versions...</div>\
		<hr>\
		<p class='text-muted'>&copy; Finbyz ERP is powered by opensource technologies </p> \
		</div>", frappe.app));

		frappe.ui.misc.about_dialog = d;

		frappe.ui.misc.about_dialog.on_page_show = function() {
			if(!frappe.versions) {
				frappe.call({
					method: "frappe.utils.change_log.get_versions",
					callback: function(r) {
						show_versions(r.message);
					}
				})
			} else {
				show_versions(frappe.versions);
			}
		};

		var show_versions = function(versions) {
			var $wrap = $("#about-app-versions").empty();
			$.each(Object.keys(versions).sort(), function(i, key) {
				var v = versions[key];
				if(v.branch) {
					var text = $.format('<p><b>{0}:</b> v{1} ({2})<br></p>',
						[v.title, v.branch_version || v.version, v.branch])
				} else {
					var text = $.format('<p><b>{0}:</b> v{1}<br></p>',
						[v.title, v.version])
				}
				$(text).appendTo($wrap);
			});

			frappe.versions = versions;
		}

	}

	frappe.ui.misc.about_dialog.show();

}
