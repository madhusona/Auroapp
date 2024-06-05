import frappe
from frappe.utils.data import ceil

def get_context(context):

    categories = frappe.get_list("Unit", fields=["type"], group_by="type",order_by="type ASC")
    context.categories = categories
    address = frappe.get_list("Unit", fields=["parent1"], group_by="parent1", order_by="parent1 asc")
    context.address = address
    
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
        elif search_by == "email_id":
            search_by_field = "email_id"
        elif search_by == "mobile_id":
            search_by_field = "mobile_id"
        else:
            # Default to first_name if search_by is not provided or invalid
            search_by_field = "first_name"
    else:
        # Default to first_name if search_by is not provided
        search_by_field = "first_name"

    if search_name:
        context.search_name = search_name

    print(context.search_name)
    # Pagination
    page_length = 9  # Number of records per page
    current_page = frappe.form_dict.get("page", 1)  # Current page number, default is 1
    start = (int(current_page) - 1) * page_length

    # Fetch records based on filters and pagination
    filters_to_use = {}  # Create a copy of the original filters
    if status:
        filters_to_use["type"] = status
    if auroville_address:
        filters_to_use["parent1"] = auroville_address
    if search_by_field == "email_id":
        filters_to_use["email"] = ["like", "%" + search_name + "%"]
    if search_by_field == "mobile_id":
        filters_to_use["phone"] = ["like", "%" + search_name + "%"]
    if search_by_field == "first_name":
        filters_to_use["name1"] = ["like", "%" + (search_name or "") + "%"]


    
 
    
    #total_records = frappe.db.sql(total_records_query)[0][0]
    total_records=frappe.db.count('Unit',filters=filters_to_use)
    print(total_records)
    context.total_records = total_records
    total_pages = ceil(total_records / page_length)

    # Fetch records
    records = frappe.db.get_list(
        "Unit",
        filters=filters_to_use,        
        fields=[
            "name1", "type", "parent1",
            "email", "phone","communtiy"
        ],
        order_by="name1 ASC",
        group_by=None,
        start=start,
        page_length=page_length
    )

    # Pass context variables
    context.records = records
    context.total_pages = total_pages
    context.current_page = current_page
    context.no_cache = 1
    return context