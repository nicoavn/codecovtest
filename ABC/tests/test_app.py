import datetime as dt
from decimal import Decimal as D

import arrow

from ..model import entities as ents


class TestJSONCustomization:
    """
    Test app customization/hack to be able to pass custom json serlization functions to
    psycopg2.
    """

    def test_datetime_serialization(self):
        user = ents.User.testing_create(
            settings={
                'datetime': dt.datetime(2016, 1, 1),
                'date': dt.date(2016, 1, 2),
                'arrow': arrow.get(2016, 1, 3, 10, 11, 12),
            }
        )

        # The JSON parser will serialize to ISO format, but won't deserialize to datetime.
        # That should be fine for now.
        assert user.settings['datetime'] == '2016-01-01T00:00:00'
        assert user.settings['date'] == '2016-01-02'
        assert user.settings['arrow'] == '2016-01-03T10:11:12+00:00'

    def test_decimal_roundtrip(self):
        user = ents.User.testing_create(settings={'foo': D('123.45')})

        user_id = user.id

        ents.db.session.remove()

        user = ents.User.query.get(user_id)

        assert user.settings['foo'] == D('123.45')
