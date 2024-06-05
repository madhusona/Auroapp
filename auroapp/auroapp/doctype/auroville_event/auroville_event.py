# Copyright (c) 2024, Madusudhanan B and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from frappe import _
from frappe.contacts.doctype.contact.contact import get_default_contact
from frappe.desk.doctype.notification_settings.notification_settings import (
    is_email_notifications_enabled_for_type,
)
from frappe.desk.reportview import get_filters_cond

from frappe.utils import (
    add_days,
    add_months,
    cint,
    cstr,
    date_diff,
    format_datetime,
    get_datetime_str,
    getdate,
    now_datetime,
    nowdate,
)
from frappe.utils.user import get_enabled_system_users
from dateutil import parser

weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
communication_mapping = {
    "": "Event",
    "Event": "Event",
    "Meeting": "Meeting",
    "Call": "Phone",
    "Sent/Received Email": "Email",
    "Other": "Other",
}



class AurovilleEvent(Document):
    pass


@frappe.whitelist(allow_guest=True)
def get_events(start, end, user=None, for_reminder=False, filters=None) -> list[frappe._dict]:
    if not user:
        user = frappe.session.user

    if isinstance(filters, str):
        filters = json.loads(filters)

    #filter_condition = get_filters_cond("Event", filters, [])

    tables = ["`tabAuroville Event`"]
    

    events = frappe.db.sql(
        """
        SELECT `tabAuroville Event`.name,
                `tabAuroville Event`.subject,
                `tabAuroville Event`.starts_on,
                `tabAuroville Event`.ends_on,
                `tabAuroville Event`.all_day,
                `tabAuroville Event`.event_type,
                `tabAuroville Event`.repeat_this_event,
                `tabAuroville Event`.repeat_on,
                `tabAuroville Event`.repeat_till,
                `tabAuroville Event`.monday,
                `tabAuroville Event`.tuesday,
                `tabAuroville Event`.wednesday,
                `tabAuroville Event`.thursday,
                `tabAuroville Event`.friday,
                `tabAuroville Event`.saturday,
                `tabAuroville Event`.sunday
        FROM {tables}
        WHERE (
                (
                    (date(`tabAuroville Event`.starts_on) BETWEEN date(%(start)s) AND date(%(end)s))
                    OR (date(`tabAuroville Event`.ends_on) BETWEEN date(%(start)s) AND date(%(end)s))
                    OR (
                        date(`tabAuroville Event`.starts_on) <= date(%(start)s)
                        AND date(`tabAuroville Event`.ends_on) >= date(%(end)s)
                    )
                )
                OR (
                    date(`tabAuroville Event`.starts_on) <= date(%(start)s)
                    AND `tabAuroville Event`.repeat_this_event=1
                    AND coalesce(`tabAuroville Event`.repeat_till, '3000-01-01') > date(%(start)s)
                )
            )		
        AND (
                `tabAuroville Event`.event_type='Public'
                OR `tabAuroville Event`.owner=%(user)s
                
            )
        AND `tabAuroville Event`.status='Open'
        ORDER BY `tabAuroville Event`.starts_on""".format(
            tables=", ".join(tables),
            
        ),
        {
            "start": start,
            "end": end,
            "user": user,
        },
        as_dict=1,
    )

    # process recurring events
    start = start.split(" ", 1)[0]
    end = end.split(" ", 1)[0]
    add_events = []
    remove_events = []

    def add_event(e, date):
        new_event = e.copy()

        enddate = (
            add_days(date, int(date_diff(e.ends_on.split(" ", 1)[0], e.starts_on.split(" ", 1)[0])))
            if (e.starts_on and e.ends_on)
            else date
        )

        new_event.starts_on = date + " " + e.starts_on.split(" ")[1]
        new_event.ends_on = new_event.ends_on = enddate + " " + e.ends_on.split(" ")[1] if e.ends_on else None

        add_events.append(new_event)

    for e in events:
        if e.repeat_this_event:
            e.starts_on = get_datetime_str(e.starts_on)
            e.ends_on = get_datetime_str(e.ends_on) if e.ends_on else None

            event_start, time_str = get_datetime_str(e.starts_on).split(" ")

            repeat = "3000-01-01" if cstr(e.repeat_till) == "" else e.repeat_till

            if e.repeat_on == "Yearly":
                start_year = cint(start.split("-", 1)[0])
                end_year = cint(end.split("-", 1)[0])

                # creates a string with date (27) and month (07) eg: 07-27
                event_start = "-".join(event_start.split("-")[1:])

                # repeat for all years in period
                for year in range(start_year, end_year + 1):
                    date = str(year) + "-" + event_start
                    if (
                        getdate(date) >= getdate(start)
                        and getdate(date) <= getdate(end)
                        and getdate(date) <= getdate(repeat)
                    ):
                        add_event(e, date)

                remove_events.append(e)

            if e.repeat_on == "Monthly":
                # creates a string with date (27) and month (07) and year (2019) eg: 2019-07-27
                year, month = start.split("-", maxsplit=2)[:2]
                date = f"{year}-{month}-" + event_start.split("-", maxsplit=3)[2]

                # last day of month issue, start from prev month!
                try:
                    getdate(date)
                except Exception:
                    # Don't show any message to the user
                    frappe.clear_last_message()

                    date = date.split("-")
                    date = date[0] + "-" + str(cint(date[1]) - 1) + "-" + date[2]

                start_from = date
                for i in range(int(date_diff(end, start) / 30) + 3):
                    if (
                        getdate(date) >= getdate(start)
                        and getdate(date) <= getdate(end)
                        and getdate(date) <= getdate(repeat)
                        and getdate(date) >= getdate(event_start)
                    ):
                        add_event(e, date)

                    date = add_months(start_from, i + 1)
                remove_events.append(e)

            if e.repeat_on == "Weekly":
                for cnt in range(date_diff(end, start) + 1):
                    date = add_days(start, cnt)
                    if (
                        getdate(date) >= getdate(start)
                        and getdate(date) <= getdate(end)
                        and getdate(date) <= getdate(repeat)
                        and getdate(date) >= getdate(event_start)
                        and e[weekdays[getdate(date).weekday()]]
                    ):
                        add_event(e, date)

                remove_events.append(e)

            if e.repeat_on == "Daily":
                for cnt in range(date_diff(end, start) + 1):
                    date = add_days(start, cnt)
                    if (
                        getdate(date) >= getdate(event_start)
                        and getdate(date) <= getdate(end)
                        and getdate(date) <= getdate(repeat)
                    ):
                        add_event(e, date)

                remove_events.append(e)

    for e in remove_events:
        events.remove(e)

    events = events + add_events

    

    for e in events:
        if isinstance(e['starts_on'], str):
            e['starts_on'] = parser.parse(e['starts_on'])

    # Sort the final events list by starts_on
    events = sorted(events, key=lambda x: x['starts_on'])

    '''
    for e in events:
        # remove weekday properties (to reduce message size)
        for w in weekdays:
            del e[w]
    '''
    return events