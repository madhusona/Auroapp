import frappe

def get_context(context):
    event_name = frappe.form_dict.get('name')
    if not event_name:
        frappe.throw("Event name is required")
    
    event = frappe.get_doc('Auroville Event', event_name)
    
    context.event = event