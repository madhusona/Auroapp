import frappe
from frappe.utils.data import ceil

def get_context(context):
    
    filters = {
        "status": ["in", ["Aurovilian", "Aurovilian Confirmed", "Aurovilian child", 
                          "Returned Aurovilian", "New comer", "New comer child", 
                          "To be new comer", "To be new comer child"]]
    }

    categories = frappe.get_list("Directory", filters=filters, fields=["status"], group_by="status")
    context.categories = categories
    address = frappe.get_list("Directory", filters=filters, fields=["auroville_address"], group_by="auroville_address", order_by="auroville_address asc")
    context.address = address
    '''if not hasattr(context, "categories"):
        categories = frappe.get_list("Directory", filters=filters, fields=["status"], group_by="status")
        context.categories = categories

    if not hasattr(context, "address"):
        address = frappe.get_list("Directory", filters=filters, fields=["auroville_address"], group_by="auroville_address", order_by="auroville_address asc")
        context.address = address
    '''
    # Extracting filters from form dictionary
    status = frappe.form_dict.get("status")
    auroville_address = frappe.form_dict.get("auroville_address")
    search_by = frappe.form_dict.get("search_by")
    search_name = frappe.form_dict.get("search_name")

    # Set context variables
    if status:
        context.category_selected = status
    if auroville_address:
        context.type_selected = auroville_address
    if search_by:
        context.search_by = search_by
        # Adjust search_by field if needed
        if search_by == "firstname":
            search_by_field = "first_name"
        elif search_by == "surname":
            search_by_field = "surname"
        elif search_by == "auroville_name":
            search_by_field = "auroville_name"
        else:
            # Default to first_name if search_by is not provided or invalid
            search_by_field = "first_name"
    else:
        # Default to first_name if search_by is not provided
        search_by_field = "first_name"

    if search_name:
        context.search_name = search_name

    # Pagination
    page_length = 9  # Number of records per page
    current_page = frappe.form_dict.get("page", 1)  # Current page number, default is 1
    limit_start = (int(current_page) - 1) * page_length

    # Fetch records based on filters and pagination
    records_filters = filters.copy()  # Create a copy of the original filters
    if status:
        records_filters["status"] = status
    if auroville_address:
        records_filters["auroville_address"] = auroville_address
    if search_by_field and search_name:
        records_filters[search_by_field] = ["like", "%" + search_name + "%"]

    total_records = frappe.db.count("Directory", filters=records_filters)
    total_pages = ceil(total_records / page_length)
    
    records = frappe.get_list("Directory", filters=records_filters, fields=["first_name", "surname", "auroville_name", "status", "auroville_address"], limit_start=limit_start, limit_page_length=page_length)

    # Pass context variables
    context.records = records
    context.total_pages = total_pages
    context.current_page = current_page
    
    return context
