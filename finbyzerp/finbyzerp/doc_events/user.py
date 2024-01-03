import frappe


def validate(self, method):
    validate_user_mobile_no(self)
    check_system_manager_role(self)


def validate_user_mobile_no(self):
    if self.mobile_no:
        if not self.mobile_no.isdigit():
            frappe.throw("Please Enter Digits Only in Mobile Number.")
        elif len(self.mobile_no) != 10:
            frappe.throw("Please Enter 10 digit Mobile Number.")


def check_system_manager_role(self):
    if self.name not in [
        "info@finbyz.com",
        "Administrator",
        "mukesh@finbyz.tech",
        "info@finbyz.tech",
    ]:
        remove_roles = []
        for role in self.roles:
            if role.role == "System Manager":
                remove_roles.append(role)

        [self.roles.remove(d) for d in remove_roles]
