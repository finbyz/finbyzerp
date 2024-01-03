from finbyzerp.finbyzerp.override.functionality.utils import get_timespan_date_range


def get_date_range(operator, value):
    timespan_map = {
        "1 week": "week",
        "1 month": "month",
        "3 months": "quarter",
        "6 months": "6 months",
        "1 year": "year",
    }
    period_map = {
        "previous": "last",
        "next": "next",
    }

    timespan = (
        period_map[operator] + " " + timespan_map[value]
        if operator != "timespan"
        else value
    )

    return get_timespan_date_range(timespan)
