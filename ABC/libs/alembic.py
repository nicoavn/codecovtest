from contextlib import contextmanager
from os import path as osp

import keg

import alembic
import alembic.config
from alembic.script import ScriptDirectory


def alembic_config(config=None):
    config = config or alembic.config.Config()
    project_src_dpath = osp.dirname(keg.current_app.root_path)
    script_location = osp.join(project_src_dpath, 'alembic')
    config.set_main_option('script_location', script_location)
    config.set_main_option('bootstrap_app', 'false')
    config.set_main_option('sqlalchemy.url', keg.current_app.config['SQLALCHEMY_DATABASE_URI'])
    return config


def alembic_upgrade(revision):
    alembic_conf = alembic_config()
    alembic.command.upgrade(alembic_conf, revision)


def alembic_apply(revision):
    """
    Stamp the current DB at the "down_revision" of the revision to be applied. Then,
    "upgrade" to the revision requested.
    This should guarantee that only the requested revision is run and nothing it depends on.
    """
    alembic_conf = alembic_config()
    scriptdir = ScriptDirectory.from_config(alembic_conf)
    script = scriptdir.get_revision(revision)
    if script.down_revision is None:
        down_revision = 'base'
    else:
        down_revision = script.down_revision

    alembic.command.stamp(alembic_conf, down_revision)
    alembic.command.upgrade(alembic_conf, revision)


@contextmanager
def alembic_automap_init(alembic_op):
    # Import inside to avoid circular imports.  ABC.libs.db imports
    # from this file.
    from .db import reflect_db

    # Use the same connection to the DB that the Alembic environment is using so that all of our
    # operations are happening withing the single Alembic-managed transaction.  The goal is that
    # multiple migrations can be ran and all will succeed or fail together.
    conn = alembic_op.get_context().connection
    Base, sa_session = reflect_db(conn)

    try:
        yield Base, sa_session
        # Flush any pending operations in the session.  No need for a commit b/c it wouldn't really
        # apply at the connection level anyway.  See below for details on why.
        sa_session.flush()
    finally:
        # Even though we are sharing the connection/transaction the Alembic environment has setup,
        # closing the session here will not affect the outer Alembic-managed transaction.  This is
        # due to the fact that the connection object maintains subtransactions.  Further reading:
        # http://docs.sqlalchemy.org/en/rel_1_0/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites # noqa
        sa_session.close()
