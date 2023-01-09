import keg
from keg.db import db
from keg_auth.model import KAPasswordType
from sqlalchemy_utils import ArrowType, EmailType

from alembic import context
from ABC.app import AABC

if keg.current_app:
    app = keg.current_app
else:
    app = AABC().init()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = db.metadata


def render_item(type_, obj, autogen_context):
    """Apply custom rendering for selected items."""

    if type_ == 'type':
        if isinstance(obj, ArrowType):
            autogen_context.imports.add('import sqlalchemy_utils as utils')
            return 'utils.ArrowType()'
        elif isinstance(obj, EmailType):
            autogen_context.imports.add('import sqlalchemy_utils as utils')
            return 'utils.EmailType()'
        elif isinstance(obj, KAPasswordType):
            autogen_context.imports.add('from keg_auth.model import KAPasswordType')
            return 'KAPasswordType()'

    # default rendering for other objects
    return False


def compare_type(context, inspected_column, metadata_column, inspected_type, metadata_type):
    """Custom compare_type function for alembic autogeneration"""
    if metadata_type == KAPasswordType or type(metadata_type) == KAPasswordType:
        # KAPasswordType throws flask app context errors during type
        # comparison, so we return False to disable type comparison
        return False
    # Returning "None" defaults to alembic's built-in type comparison
    return None


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = db.get_engines(app)[0][1]

    print("Operating on database at: {}".format(connectable.url))

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_item=render_item,
            compare_type=compare_type,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
