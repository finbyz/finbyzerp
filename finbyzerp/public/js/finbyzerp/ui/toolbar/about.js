frappe.provide("frappe.ui.misc");
frappe.ui.misc.about = function () {
	if (!frappe.ui.misc.about_dialog) {
		var d = new frappe.ui.Dialog({title: __('<img src="https://finbyz.tech/files/finbyz-tech.svg" width="180">')});

		$(d.body).html(
			repl(
				`<div>
					<p>${__("At Finbyz Tech, we are passionate about revolutionizing businesses through the latest technology.")}</p>
					<p><i class='fa fa-globe fa-fw'></i>
						${__("Website")}:
						<a href='https://finbyz.tech' target='_blank'>https://finbyz.tech</a></p>
					<p><i class='fa fa-envelope fa-fw'></i>
						Support: <a href='mailto:support@finbyz.tech'>support@finbyz.tech</a></p>
					<p><i class='fa fa-phone fa-fw'></i>
						Phone: <a href='tel:+917948912428'>079 4891 2428</a></p>
					<hr>
					<h4>${__("Installed Apps")}</h4>
					<div id='about-app-versions'>${__("Loading versions...")}</div>
					<hr>
					<p class='text-muted'>${__("&copy; Finbyz Tech Pvt. Ltd. and contributors")} </p>
					<p>
						<span><a href='https://www.linkedin.com/company/finbyz' target='_blank'><i class='fa fa-linkedin fa-fw'></i></a></span>
						<span><a href='https://www.facebook.com/FinByz' target='_blank'><i class='fa fa-facebook fa-fw'></i></a></span>
						<span><a href='https://www.instagram.com/finbyz' target='_blank'><i class='fa fa-instagram fa-fw'></i></a></span>
						<span><a href='https://twitter.com/FinByz' target='_blank'><i class='fa fa-twitter fa-fw'></i></a></span>
						<span><a href='https://www.youtube.com/@Finbyz' target='_blank'><i class='fa fa-youtube fa-fw'></i></a></span>
					</p>
					</div>`,
				frappe.app
			)
		);

		frappe.ui.misc.about_dialog = d;

		frappe.ui.misc.about_dialog.on_page_show = function () {
			if (!frappe.versions) {
				frappe.call({
					method: "frappe.utils.change_log.get_versions",
					callback: function (r) {
						show_versions(r.message);
					},
				});
			} else {
				show_versions(frappe.versions);
			}
		};

		var show_versions = function (versions) {
			var $wrap = $("#about-app-versions").empty();
			$.each(Object.keys(versions).sort(), function (i, key) {
				var v = versions[key];
				let text;
				if (v.branch) {
					text = $.format("<p><b>{0}:</b> v{1} ({2})<br></p>", [
						v.title,
						v.branch_version || v.version,
						v.branch,
					]);
				} else {
					text = $.format("<p><b>{0}:</b> v{1}<br></p>", [v.title, v.version]);
				}
				$(text).appendTo($wrap);
			});

			frappe.versions = versions;
		};
	}

	frappe.ui.misc.about_dialog.show();
};
