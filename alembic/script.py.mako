"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import context, op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    # run the data migration unless it is explicitly disabled with `-x data=false`
    if context.get_x_argument(as_dictionary=True).get('data', 'true').lower() != 'false':
        data_upgrades()

    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}

    # run the data migration unless it is explicitly disabled with `-x data=false`
    if context.get_x_argument(as_dictionary=True).get('data', 'true') != 'false':
        data_downgrades()


def data_upgrades():
    """Add any optional data upgrade migrations here!"""
    # from sqlalchemy.ext.automap import automap_base
    # from sqlalchemy.orm import Session
    # conn = op.get_bind()
    # Base = automap_base()
    # Base.prepare(conn, reflect=True)
    # session = sa.orm.Session(conn)
    # my_entity = Base.classes.my_entity
    # data = session.query(my_entity).all()


def data_downgrades():
    """Add any optional data downgrade migrations here!"""
    # metadata = sa.MetaData()
    # conn = op.get_bind()
    # metadata.reflect(conn)
    # my_table = metadata.tables['my_table']
    # data = conn.execute(my_table.select()).fetchall()
