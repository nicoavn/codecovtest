from keg_elements.testing import ColumnCheck, EntityBase

from ..model import entities as ents


class TestUser(EntityBase):
    entity_cls = ents.User
    column_checks = [
        ColumnCheck('is_verified'),
        ColumnCheck('is_enabled'),
        ColumnCheck('is_superuser'),
        ColumnCheck('session_key', unique=True),
        ColumnCheck('email', unique=True),
        ColumnCheck('password', required=False),
        ColumnCheck('name'),
        ColumnCheck('settings', required=False),
        ColumnCheck('last_login_utc', required=False),
        ColumnCheck('disabled_utc', required=False),
    ]
