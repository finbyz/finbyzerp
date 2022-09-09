(()=>{frappe.templates.navbar=`<header class="navbar navbar-expand sticky-top" role="navigation">
	<div class="container-fluid">
		<a class="navbar-brand navbar-home" href="/app">
			<img class="app-logo" style="width: {{ navbar_settings.logo_width || 24 }}px" src="/assets/finbyzerp/images/home.svg">
		</a>
		<ul class="nav navbar-nav d-none d-sm-flex" id="navbar-breadcrumbs"></ul>
		<div class="collapse navbar-collapse justify-content-end">
			<form class="form-inline fill-width justify-content-end" role="search" onsubmit="return false;">
				<div class="input-group search-bar text-muted hidden">
					<input
						id="navbar-search"
						type="text"
						class="form-control"
						placeholder="{%= __("Search or type a command (Ctrl + G)") %}"
						aria-haspopup="true"
					>
					<span class="search-icon">
						<svg class="icon icon-sm"><use xlink:href="#icon-search"></use></svg>
					</span>
				</div>
			</form>
			<ul class="navbar-nav">
				<li class="nav-item dropdown dropdown-notifications dropdown-mobile hidden">
					<a
						class="nav-link notifications-icon text-muted"
						data-toggle="dropdown"
						aria-haspopup="true"
						aria-expanded="true"
						href="#"
						onclick="return false;">
						<span class="notifications-seen">
							<svg class="icon icon-md "><use href="#icon-notification"></use></svg>
						</span>
						<span class="notifications-unseen">
							<svg class="icon icon-md "><use href="#icon-notification-with-indicator"></use></svg>
						</span>
					</a>
					<div class="dropdown-menu notifications-list dropdown-menu-right" role="menu">
						<div class="notification-list-header">
							<div class="header-items"></div>
							<div class="header-actions"></div>
						</div>
						<div class="notification-list-body">
							<div class="panel-notifications"></div>
							<div class="panel-events"></div>
						</div>
					</div>
				</li>
				<li class="nav-item dropdown dropdown-message dropdown-mobile hidden">
					<a
						class="nav-link notifications-icon text-muted"
						data-toggle="dropdown"
						aria-haspopup="true"
						aria-expanded="true"
						href="#"
						onclick="return false;">
						<span>
							<svg class="icon icon-md"><use href="#icon-small-message"></use></svg>
						</span>
					</a>
				</li>
				<li class="vertical-bar d-none d-sm-block"></li>
				<li class="nav-item dropdown dropdown-help dropdown-mobile d-none d-lg-block">
					<a class="nav-link help_icon" data-toggle="dropdown" href="#" onclick="return false;">
						{{ __("Help") }}
						<span>
							<svg class="icon icon-xs"><use href="#icon-small-down"></use></svg>
						</span>
					</a>
					<div class="dropdown-menu dropdown-menu-right" id="toolbar-help" role="menu">
						<div id="help-links"></div>
						<div class="dropdown-divider documentation-links"></div>
						{% for item in navbar_settings.help_dropdown %}
							{% if (!item.hidden) { %}
								{% if (item.route) { %}
									<a class="dropdown-item" href="{{ item.route }}">
										{%= __(item.item_label) %}
									</a>
								{% } else if (item.action) { %}
									<a class="dropdown-item" onclick="return {{ item.action }}">
										{%= __(item.item_label) %}
									</a>
								{% } else { %}
									<div class="dropdown-divider"></div>
								{% } %}
							{% } %}
						{% endfor %}
					</div>
				</li>
				<li class="nav-item dropdown dropdown-navbar-user dropdown-mobile">
					<a class="nav-link" data-toggle="dropdown" href="#" onclick="return false;">
						{{ avatar }}
					</a>
					<div class="dropdown-menu dropdown-menu-right" id="toolbar-user" role="menu">
						{% for item in navbar_settings.settings_dropdown %}
							{% if (!item.hidden) { %}
								{% if (item.route) { %}
									<a class="dropdown-item" href="{{ item.route }}">
										{%= __(item.item_label) %}
									</a>
								{% } else if (item.action) { %}
									<a class="dropdown-item" onclick="return {{ item.action }}">
										{%= __(item.item_label) %}
									</a>
								{% } else { %}
									<div class="dropdown-divider"></div>
								{% } %}
							{% } %}
						{% endfor %}
					</div>
				</li>
			</ul>
		</div>
	</div>
</header>
`;frappe.templates.page=`<div class="page-head flex">
	<div class="container-fluid">
		<div class="row flex align-center page-head-content justify-between">
			<div class="col-lg-8 col-md-12 col-sm-12 col-xs-8 page-title">
				<!-- <div class="title-image hide hidden-md hidden-lg"></div> -->
				<!-- title -->
				<span class="sidebar-toggle-btn">
					<svg class="icon icon-md sidebar-toggle-placeholder">
						<use xlink:href="#icon-menu"></use>
					</svg>
					<span class="sidebar-toggle-icon">
						<svg class="icon icon-md">
							<use xlink:href="#icon-sidebar-collapse">
							</use>
						</svg>
					</span>
				</span>
				<div class="flex fill-width title-area">
					<div>
						<div class="flex">
							<h3 class="ellipsis title-text"></h3>
							<span class="indicator-pill whitespace-nowrap"></span>
						</div>
						<div class="ellipsis sub-heading hide text-muted"></div>
					</div>
					<button class="btn btn-default more-button hide">
						<svg class="icon icon-sm">
							<use xlink:href="#icon-dot-horizontal">
							</use>
						</svg>
					</button>
				</div>
			</div>
			<div class="col-lg-4 col-12  flex col page-actions justify-content-end">
				<!-- buttons -->
				<div class="custom-actions hide "></div>
				<div class="standard-actions flex">
					<span class="page-icon-group hide hidden-xs hidden-sm"></span>
					<div class="menu-btn-group hide">
						<button type="button" class="btn btn-default icon-btn" data-toggle="dropdown" aria-expanded="false">
							<span>
								<span class="menu-btn-group-label">
									<svg class="icon icon-sm">
										<use xlink:href="#icon-dot-horizontal">
										</use>
									</svg>
								</span>
							</span>
						</button>
						<ul class="dropdown-menu dropdown-menu-right" role="menu"></ul>
					</div>
					<button class="btn btn-secondary btn-default btn-sm hide"></button>
					<div class="actions-btn-group hide">
						<button type="button" class="btn btn-primary btn-sm" data-toggle="dropdown" aria-expanded="false">
							<span class="hidden-xs">
								<span class="actions-btn-group-label">{%= __("Actions") %}</span>
								<svg class="icon icon-xs">
									<use xlink:href="#icon-select">
									</use>
								</svg>
							</span>
						</button>
						<ul class="dropdown-menu dropdown-menu-right" role="menu">
						</ul>
					</div>
					<button class="btn btn-primary btn-sm hide primary-action"></button>
				</div>
			</div>
		</div>
	</div>
</div>
<div class="container-fluid page-body">
	<div class="page-toolbar hide">
		<div class="container">
		</div>
	</div>
	<div class="page-wrapper">
		<div class="page-content">
			<div class="workflow-button-area btn-group pull-right hide"></div>
			<div class="clearfix"></div>
		</div>
	</div>
</div>`;frappe.provide("frappe.ui.misc");frappe.ui.misc.about=function(){if(!frappe.ui.misc.about_dialog){var t=new frappe.ui.Dialog({title:__('<img src="https://finbyz.tech/files/finbyz-tech.svg" width="180">')});$(t.body).html(repl("<div>		<p>"+__("At Finbyz Tech, we are passionate about revolutionizing businesses through the latest technology.")+"</p>  		<p><i class='fa fa-globe fa-fw'></i>			Website: <a href=' https://finbyz.tech' target='_blank'> https://finbyz.tech</a></p>		<p><i class='fa fa-solid fa-envelope fa-fw'></i>			Support: <a href='support@finbyz.tech' target='_blank'>support@finbyz.tech</a></p>		<p><i class='fa fa-phone fa-fw'></i>			Phone:<a href='tel:079 48912428'> 079 48912428</a></p>		<hr>		<h4>Installed Apps</h4>		<div id='about-app-versions'>Loading versions...</div>		<hr>		<p class='text-muted'>&copy; Finbyz ERP is powered by opensource technologies </p> 		</div>",frappe.app)),frappe.ui.misc.about_dialog=t,frappe.ui.misc.about_dialog.on_page_show=function(){frappe.versions?e(frappe.versions):frappe.call({method:"frappe.utils.change_log.get_versions",callback:function(i){e(i.message)}})};var e=function(i){var a=$("#about-app-versions").empty();$.each(Object.keys(i).sort(),function(n,o){var s=i[o];if(s.branch)var r=$.format("<p><b>{0}:</b> v{1} ({2})<br></p>",[s.title,s.branch_version||s.version,s.branch]);else var r=$.format("<p><b>{0}:</b> v{1}<br></p>",[s.title,s.version]);$(r).appendTo(a)}),frappe.versions=i}}frappe.ui.misc.about_dialog.show()};$(window).on("load",function(){setTimeout(function(){$('div[data-page-route="Form/User"] span[data-label="Duplicate"]').closest("li").hide()},1500)});$(".dt-scrollable").ready(function(){setTimeout(function(){var t=$(window).height(),e=t-$(".page-form").height(),i=e-200;$(".dt-scrollable").attr("style","height: 100px !important")},10)});frappe.ui.keys.add_shortcut({description:"Focus on search field",shortcut:"alt+f",action:()=>{let t=document.querySelector("div.page-form.flex > div:nth-child(1)> input");t&&t.focus()}});frappe.provide("frappe.pages");frappe.provide("frappe.views");window.cur_page=null;frappe.views.Container=class{constructor(){this.container=$("#body").get(0),this.page=null,this.pagewidth=$(this.container).width(),this.pagemargin=50;var e=this;$(document).on("page-change",function(){var i=frappe.get_route_str();$("body").attr("data-route",i),$("body").attr("data-sidebar",e.has_sidebar()?1:0)}),$(document).bind("rename",function(i,a,n,o){frappe.breadcrumbs.rename(a,n,o)})}add_page(e){if(e!="Workspaces"){var i=$('<div class="content page-container hide_icon_bar"></div>').attr("id","page-"+e).attr("data-page-route",e).hide().appendTo(this.container).get(0);i.label=e,frappe.pages[e]=i}else{var i=$('<div class="content page-container"></div>').attr("id","page-"+e).attr("data-page-route",e).hide().appendTo(this.container).get(0);i.label=e,frappe.pages[e]=i}return i}change_to(e){if(cur_page=this,this.page&&this.page.label===e){$(this.page).trigger("show");return}var i=this;if(e.tagName)var a=e;else var a=frappe.pages[e];if(!a){console.log(__("Page not found")+": "+e);return}return window.cur_dialog&&cur_dialog.display&&!cur_dialog.keep_open&&(cur_dialog.minimizable?cur_dialog.is_minimized||cur_dialog.toggle_minimize():cur_dialog.hide()),this.page&&this.page!=a&&($(this.page).hide(),$(this.page).trigger("hide")),(!this.page||this.page!=a)&&(this.page=a,$(this.page).show()),$(document).trigger("page-change"),this.page._route=frappe.router.get_sub_path(),$(this.page).trigger("show"),!this.page.disable_scroll_to_top&&frappe.utils.scroll_to(0),frappe.breadcrumbs.update(),this.page}has_sidebar(){var e=0,i=frappe.get_route_str();if(e=frappe.ui.pages[i]&&!frappe.ui.pages[i].single_column,!e){var a=i.split("/").slice(0,2).join("/");e=$(`.page-container[data-page-route="${a}"] .layout-side-section`).length?1:0}return e}};frappe.request.report_error=function(t,e){var i=JSON.parse(t.responseText),a;if(i.exc){try{a=(JSON.parse(i.exc)||[]).join(`
`)}catch(s){a=i.exc}delete i.exc}else a="";var n=function(){var s=["<h5>Please type some additional information that could help us reproduce this issue:</h5>",'<div style="min-height: 100px; border: 1px solid #bbb; 				border-radius: 5px; padding: 15px; margin-bottom: 15px;"></div>',"<hr>","<h5>App Versions</h5>","<pre>"+JSON.stringify(frappe.boot.versions,null,"	")+"</pre>","<h5>Route</h5>","<pre>"+frappe.get_route_str()+"</pre>","<hr>","<h5>Error Report</h5>","<pre>"+a+"</pre>","<hr>","<h5>Request Data</h5>","<pre>"+JSON.stringify(e,null,"	")+"</pre>","<hr>","<h5>Response JSON</h5>","<pre>"+JSON.stringify(i,null,"	")+"</pre>"].join(`
`),r=new frappe.views.CommunicationComposer({subject:"Error Report ["+frappe.datetime.nowdate()+"]",recipients:o,txt:s,doc:{doctype:"User",name:frappe.session.user}});r.dialog.$wrapper.css("z-index",cint(frappe.msg_dialog.$wrapper.css("z-index"))+1)};if(a){var o=frappe.boot.error_report_email;e=frappe.request.cleanup_request_opts(e),frappe.error_dialog||(frappe.error_dialog=new frappe.ui.Dialog({title:__("Server Error"),primary_action_label:__("Report"),primary_action:()=>{o?n():frappe.msgprint(__("Support Email Address Not Specified")),frappe.error_dialog.hide()}}),frappe.error_dialog.wrapper.classList.add("msgprint-dialog"));let s=strip(a).split(`
`);frappe.error_dialog.$body.html(s[s.length-1]),frappe.error_dialog.show()}};})();
//# sourceMappingURL=finbyzerp.bundle.WPKLVFFK.js.map
