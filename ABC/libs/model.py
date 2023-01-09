from keg.db import db
from keg_elements.db.mixins import DefaultColsMixin, MethodsMixin
from sqlalchemy.dialects.postgresql import insert as pgsql_insert
from sqlalchemy.inspection import inspect


class EntityMixin(DefaultColsMixin, MethodsMixin):
    @classmethod
    def upsert(cls, values=None, on_conflict_do='update', index_elements=None, **kwargs):
        if index_elements is None:
            index_elements = cls.__upsert_index_elements__

        if values is None:
            values = kwargs

        primary_key_col = inspect(cls).primary_key[0]
        stmt = pgsql_insert(cls.__table__).returning(primary_key_col).values(**values)

        assert on_conflict_do in ('nothing', 'update')
        if on_conflict_do == 'update':
            stmt = stmt.on_conflict_do_update(index_elements=index_elements, set_=values)
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)

        result = db.session.execute(stmt)

        return result.scalar()


def tc_relation(kwargs, rel_col_name, rel_ent_cls):
    id_col_name = f'{rel_col_name}_id'
    rel_name_dunder = f'{rel_col_name}__'

    if id_col_name not in kwargs and rel_col_name not in kwargs:
        rel_keys = [key for key in kwargs.keys() if key.startswith(rel_name_dunder)]
        rel_kwargs = {key.replace(rel_name_dunder, '', 1): kwargs.pop(key) for key in rel_keys}
        rel_ent_inst = rel_ent_cls.testing_create(**rel_kwargs)
        kwargs[id_col_name] = rel_ent_inst.id

    return kwargs
