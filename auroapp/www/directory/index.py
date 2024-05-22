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
    filters_to_use = filters.copy()  # Create a copy of the original filters
    if status:
        filters_to_use["status"] = status
    if auroville_address:
        filters_to_use["auroville_address"] = auroville_address

    # Construct search condition
    or_filters = None
    if search_name:
        if search_by_field == "email_id":
            or_filters = [
                ["auroville_email_id", "like", "%" + search_name + "%"],
                ["email_id", "like", "%" + search_name + "%"],
                ["other_email_id", "like", "%" + search_name + "%"]
            ]
        elif search_by_field == "mobile_id":
            or_filters = [
                ["phone_number_i", "like", "%" + search_name + "%"],
                ["phone_number_ii", "like", "%" + search_name + "%"],
            ]
            
        else:
            # Single condition for other search fields
            filters_to_use[search_by_field] = ["like", "%" + search_name + "%"]
          
    #or_conditions = ' OR '.join([f"`{field}` LIKE {frappe.db.escape(condition)}" for field, _, condition in or_filters]) if or_filters else ''

    where_clauses = []

    for field, value in filters_to_use.items():
        if isinstance(value, list):
            if value[0] == "in":
                where_clauses.append(f"`{field}` IN ({', '.join(frappe.db.escape(v) for v in value[1])})")
            else:
                where_clauses.append(f"`{field}` LIKE {frappe.db.escape(value[1])}")
        else:
            where_clauses.append(f"`{field}` LIKE {frappe.db.escape(value)}")

    where_clause = ' AND '.join(where_clauses)
    or_conditions = ''

    # Constructing the first condition with AND operator
    if or_filters:
        field, _, condition = or_filters[0]
        or_conditions += f"`{field}` LIKE {frappe.db.escape(condition)}"

    # Constructing the rest of the conditions with OR operator
        for field, _, condition in or_filters[1:]:
            or_conditions += f" OR `{field}` LIKE {frappe.db.escape(condition)}"
    
    total_records_query = f"""
    SELECT COUNT(*)
    FROM `tabDirectory`
    WHERE {where_clause}
    {' AND (' + or_conditions + ')' if or_conditions else ''}
"""

    
    
    total_records = frappe.db.sql(total_records_query)[0][0]
    context.total_records = total_records
    total_pages = ceil(total_records / page_length)

    # Fetch records
    records = frappe.db.get_list(
        "Directory",
        filters=filters_to_use,
        or_filters=or_filters,
        fields=[
            "first_name", "surname", "auroville_name", "status",
            "auroville_address", "profile_photo", "auroville_email_id",
            "email_id", "other_email_id", "phone_number_ii", "phone_number_i"
        ],
        order_by="",
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