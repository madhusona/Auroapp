import frappe

def route_redirect():
    
    user = frappe.session.user
    roles = frappe.get_roles(user)
    
    if "Aurovilian" in roles:
        print("sdfsdf")
        frappe.local.response["home_page"] = "/directory"