import datetime as dt
import decimal

import arrow
import flask.json


class JSONEncoder(flask.json.JSONEncoder):
    """
    The Flask JSONEncoder but puts dates in iso format instead of http date format.
    """

    def default(self, obj):
        if isinstance(obj, (dt.datetime, dt.date, arrow.Arrow)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)


class JSONDecoder(flask.json.JSONDecoder):
    """
    A custom JSON decoder that will convert floats to Decimals.
    """

    def __init__(self, *args, **kwargs):
        # Same as simplejson.loads(..., use_decimal=True)
        kwargs.setdefault('parse_float', decimal.Decimal)
        super().__init__(*args, **kwargs)
