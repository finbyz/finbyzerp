import frappe
@frappe.whitelist()
def get_desktop_settings():
    from frappe.config import get_modules_from_all_apps_for_user
    from frappe.desk.moduleview import get_home_settings, get_links
    all_modules = get_modules_from_all_apps_for_user()
    home_settings = get_home_settings()
    # module_map = {'Desk':'/files/desk_icon.png','Users and Permissions':'/files/desk_icon.png','Accounts':'icon finbyz-accounting','Getting Started':'icon finbyz-getting_started'}
    module_map = {'Desk':'icon finbyz-desk','Users and Permissions':'icon finbyz-users-and-permissions', \
        'Accounts':'icon finbyz-accounting','Getting Started':'icon finbyz-getting_started', \
        'Learn': 'icon finbyz-learn','Tools': 'icon finbyz-tools',  'Social': 'icon finbyz-social',  \
        'Leaderboard': 'icon finbyz-leaderboard','dashboard': 'icon finbyz-dashboard', \
        'Selling': 'icon finbyz-selling', 'Buying': 'icon finbyz-buying','Stock': 'icon finbyz-stock',\
        'Assets': 'icon finbyz-assets','Projects': 'icon finbyz-projects','CRM': 'icon finbyz-crm', \
        'Support': 'icon finbyz-support','HR': 'icon finbyz-hr', 'Quality Management': 'icon finbyz-quality-management', \
        'Manufacturing': 'icon finbyz-manufacturing', 'Help': 'icon finbyz-help', 'Chemical': 'icon finbyz-chemical', \
        'Exim': 'icon finbyz-exim', 'Settings' : 'icon finbyz-settings', 'Website' : 'icon finbyz-website', \
        'Customization' : 'icon finbyz-customization','Marketplace': 'icon finbyz-marketplace', \
        'Integrations':'icon finbyz-integrations','Core':'icon finbyz-developer', \
        'Ceramic': 'icon finbyz-ceramic','Finbyzweb': 'icon finbyz-finbyzweb',\
        'Engineering': 'icon finbyz-engineering','Transport':'icon finbyz-transport','Education': 'icon finbyz-education'}

    modules_by_name = {}
    for m in all_modules:
        if m['module_name'] in module_map.keys():
            m['icon'] = module_map[m['module_name']]
        modules_by_name[m['module_name']] = m
    module_categories = ['Modules', 'Domains', 'Places', 'Administration']
    user_modules_by_category = {}

    user_saved_modules_by_category = home_settings.modules_by_category or {}
    user_saved_links_by_module = home_settings.links_by_module or {}

    def apply_user_saved_links(module):
        module = frappe._dict(module)
        all_links = get_links(module.app, module.module_name)
        module_links_by_name = {}
        for link in all_links:
            module_links_by_name[link['name']] = link

        if module.module_name in user_saved_links_by_module:
            user_links = frappe.parse_json(user_saved_links_by_module[module.module_name])
            module.links = [module_links_by_name[l] for l in user_links if l in module_links_by_name]

        return module

    for category in module_categories:
        if category in user_saved_modules_by_category:
            user_modules = user_saved_modules_by_category[category]
            user_modules_by_category[category] = [apply_user_saved_links(modules_by_name[m]) \
                for m in user_modules if modules_by_name.get(m)]
        else:
            user_modules_by_category[category] = [apply_user_saved_links(m) \
                for m in all_modules if m.get('category') == category]

    # filter out hidden modules
    if home_settings.hidden_modules:
        for category in user_modules_by_category:
            hidden_modules = home_settings.hidden_modules or []
            modules = user_modules_by_category[category]
            user_modules_by_category[category] = [module for module in modules if module.module_name not in hidden_modules]

    return user_modules_by_category


@frappe.whitelist()
def get_options_for_global_modules():
    from frappe.config import get_modules_from_all_apps
    all_modules = get_modules_from_all_apps()

    blocked_modules = frappe.get_doc('User', 'Administrator').get_blocked_modules()

    module_map = {'Desk':'icon finbyz-desk','Users and Permissions':'icon finbyz-users-and-permissions', \
    'Accounts':'icon finbyz-accounting','Getting Started':'icon finbyz-getting_started', \
    'Learn': 'icon finbyz-learn','Tools': 'icon finbyz-tools',  'Social': 'icon finbyz-social', \
    'Leaderboard': 'icon finbyz-leaderboard','dashboard': 'icon finbyz-dashboard', 'Selling': 'icon finbyz-selling', \
    'Buying': 'icon finbyz-buying','Stock': 'icon finbyz-stock','Assets': 'icon finbyz-assets', \
    'Projects': 'icon finbyz-projects','CRM': 'icon finbyz-crm', 'Support': 'icon finbyz-support',\
    'HR': 'icon finbyz-hr', 'Quality Management': 'icon finbyz-quality-management', \
    'Manufacturing': 'icon finbyz-manufacturing', 'Help': 'icon finbyz-help', 'Chemical': 'icon finbyz-chemical', \
    'Exim': 'icon finbyz-exim','Engineering': 'icon finbyz-engineering','Transport':'icon finbyz-transport'}
    
    # frappe.msgprint(str(all_modules))
    options = []
    for module in all_modules:
        module = frappe._dict(module)
        # frappe.msgprint(str(module))
        options.append({
            'category': module.category,
            'label': module.label,
            'value': module.module_name,
            'checked': module.module_name not in blocked_modules
        })

    return options
