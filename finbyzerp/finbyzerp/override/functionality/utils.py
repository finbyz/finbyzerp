from frappe.utils import nowdate
from frappe.utils.data import (
    get_first_day_of_week,
    add_to_date,
    get_first_day,
    get_last_day_of_week,
    get_quarter_start,
    get_last_day,
    get_quarter_ending,
    get_year_ending,
    get_year_start,
)


def get_timespan_date_range(timespan):
    today = nowdate()
    date_range_map = {
        "last week": lambda: (
            get_first_day_of_week(add_to_date(today, days=-7)),
            get_last_day_of_week(add_to_date(today, days=-7)),
        ),
        "last month": lambda: (
            get_first_day(add_to_date(today, months=-1)),
            get_last_day(add_to_date(today, months=-1)),
        ),
        "last quarter": lambda: (
            get_quarter_start(add_to_date(today, months=-3)),
            get_quarter_ending(add_to_date(today, months=-3)),
        ),
        "last 6 months": lambda: (
            get_quarter_start(add_to_date(today, months=-6)),
            get_quarter_ending(add_to_date(today, months=-3)),
        ),
        "last year": lambda: (
            get_year_start(add_to_date(today, years=-1)),
            get_year_ending(add_to_date(today, years=-1)),
        ),
        "yesterday": lambda: (add_to_date(today, days=-1),) * 2,
        "today": lambda: (today, today),
        "tomorrow": lambda: (add_to_date(today, days=1),) * 2,
        # "this week": lambda: (get_first_day_of_week(today), today),
        "this week": lambda: (
            get_first_day_of_week(today),
            get_last_day_of_week(get_first_day_of_week(today)),
        ),
        # "this month": lambda: (get_first_day(today), today),
        "this month": lambda: (
            get_first_day(today),
            get_last_day(get_first_day(today)),
        ),
        # "this quarter": lambda: (get_quarter_start(today), today),
        "this quarter": lambda: (
            get_quarter_start(today),
            get_quarter_ending(get_quarter_start(today)),
        ),
        # "this year": lambda: (get_year_start(today), today),
        "this year": lambda: (
            get_year_start(today),
            get_year_ending(get_year_start(today)),
        ),
        "next week": lambda: (
            get_first_day_of_week(add_to_date(today, days=7)),
            get_last_day_of_week(add_to_date(today, days=7)),
        ),
        "next month": lambda: (
            get_first_day(add_to_date(today, months=1)),
            get_last_day(add_to_date(today, months=1)),
        ),
        "next quarter": lambda: (
            get_quarter_start(add_to_date(today, months=3)),
            get_quarter_ending(add_to_date(today, months=3)),
        ),
        "next 6 months": lambda: (
            get_quarter_start(add_to_date(today, months=3)),
            get_quarter_ending(add_to_date(today, months=6)),
        ),
        "next year": lambda: (
            get_year_start(add_to_date(today, years=1)),
            get_year_ending(add_to_date(today, years=1)),
        ),
    }

    if timespan in date_range_map:
        return date_range_map[timespan]()
