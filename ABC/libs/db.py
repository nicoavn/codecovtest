import logging
import os
import os.path as osp
import subprocess
from collections import namedtuple
from contextlib import contextmanager
from decimal import Decimal as D
from pathlib import Path
from sys import platform

import sqlalchemy as sa
import sqlalchemy.engine.url
import sqlalchemy.orm as sa_orm
from keg import current_app
from keg.db import db
from keg.utils import classproperty
from keg_elements.db.mixins import MethodsMixin
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base

from .alembic import alembic_upgrade

log = logging.getLogger(__name__)


class PostgresBase:
    if platform == "linux" or platform == "linux2":
        postgresql_versions_dpath = Path('/usr/lib/postgresql')
    elif platform == "darwin":
        postgresql_versions_dpath = Path('/Library/PostgreSQL')

    def __init__(self, db_engine):
        self.errors = []
        self.db_engine = db_engine or db.engine
        self.db_url = self.db_engine.url
        self.pg_bin_dpath = self.find_bin_dir()

    def find_bin_dir(self):
        version_dirs = [x for x in self.postgresql_versions_dpath.iterdir() if x.is_dir()]
        # convert directories to Decimals so we can sort numerically and in reverse order
        postgres_versions = [D(x.name) for x in version_dirs]
        latest_version = sorted(postgres_versions).pop()
        return self.postgresql_versions_dpath.joinpath(str(latest_version), 'bin')

    def get_table_list_from_db(self, schema):
        """
        return a list of table names from the current
        databases public schema
        """
        sql = "select table_name from information_schema.tables " "where table_schema='{}'".format(
            schema
        )
        return [name for (name,) in self.db_engine.execute(sql)]

    def pg_sub_run(self, pg_cmd, pg_cmd_args):
        url = self.db_engine.url
        env = os.environ.copy()
        call_args = ['{}/{}'.format(self.pg_bin_dpath, pg_cmd)]

        if url.username:
            call_args += ['-U', url.username]

        if url.password:
            env['PGPASSWORD'] = url.password

        if url.host:
            call_args += ['--host', url.host]

        if url.port:
            call_args += ['--port', str(url.port)]

        call_args.extend(pg_cmd_args)

        log.debug('run subprocess: {}'.format(call_args))
        completed = subprocess.run(
            call_args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        log.debug('stdout: %s', completed.stdout)
        log.debug('stderr: %s', completed.stderr)

        if completed.returncode != 0:
            self.errors.append('Exit code: {}'.format(completed.returncode))
            self.errors.append('--------STDOUT---------')
            self.errors.append(completed.stdout.decode('utf-8'))
            self.errors.append('--------STDERR---------')
            self.errors.append(completed.stderr.decode('utf-8'))


class PostgresRestore(PostgresBase):
    """
    Goals:
        1. get pg_restore to run with ZERO errors/warnings unless those errors/warnings actually
           matter.
        2. The restored DB should match the backed up DB exactly except for ownership.
    Problems identified:
    * delete DB & recreate runs into issues because of active connections to the DB which can only
      be killed by a postgresql superuser (which the devs running ansible shouldn't be).
    * clear_db() which drops the schema and recreates it is an option BUT only if the user owns the
      schema being dropped.  That is a solvable problem, but becomes more complicated when you
      have a production schema owned by "shentel" which is what you would want but then you need the
      beta user to restore.  Could probably solve through the use of group roles if desired but that
      might limit the ability to separate someone who has access to beta from keeping out of
      production.
    * using -c in the restore command would clear existing objects (which is great) but might leave
      extras in the current DB that were not being restored.  That may or not be an issue for you
      but my goal was to have the db.
    * Using pg_restore without specifing the schema (-n public) results in errors relating to
      ownership of plpgsql extension.  See:
        * http://dba.stackexchange.com/questions/84798/how-to-make-pg-dump-skip-extension
        * http://www.postgresql.org/message-id/E1VuYH7-0008Rz-SV@wrigleys.postgresql.org (bug rpt)
    Known issues:
    * This method of restore results in no ownership being persisted.  All objects are owned by the
      current db user, the one running the restore.  This works well for us, but could be a problem
      in an environment which requires more fine grain ownership control.
    * It's possible there are some other DB objects (like types) which, if existing, aren't getting
      delete yet, and would cause problems on restore.  In that case, write a new sub-function for
      clear_all() to handle those types and delete them.
    * Our method of clearing assumes the restoring user has permission to delete everything.
    """

    def __init__(self, db_name=None, db_engine=None, db_manager=None, jobs=None):
        super().__init__(db_engine)
        self.db_manager = db_manager or current_app.db_manager
        self.jobs = jobs
        self.errors = []
        if not db_name or db_name == self.db_url.database:
            self.db_name = self.db_url.database
        else:
            # restoring to a different database, need to setup a new database engine
            new_url = sqlalchemy.engine.url.URL(
                self.db_url.drivername, **self.db_url.translate_connect_args()
            )
            new_url.database = db_name
            self.db_engine = sa.create_engine(new_url)
            self.db_name = db_name

    def get_seq_list_from_db(self, schema):
        """return a list of the sequence names from the current
        databases public schema
        """
        sql = (
            "select sequence_name from information_schema.sequences "
            "where sequence_schema='{}'".format(schema)
        )
        return [name for (name,) in self.db_engine.execute(sql)]

    def get_type_list_from_db(self, schema):
        """return a list of the sequence names from the current
        databases public schema
        """
        sql = """
            SELECT t.typname as type
            FROM pg_type t
            LEFT JOIN pg_catalog.pg_namespace n
                ON n.oid = t.typnamespace
            WHERE
                ( t.typrelid = 0 OR
                    (
                        SELECT c.relkind = 'c'
                        FROM pg_catalog.pg_class c
                        WHERE c.oid = t.typrelid
                    )
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM pg_catalog.pg_type el
                    WHERE el.oid = t.typelem
                        AND el.typarray = t.oid
                )
                AND n.nspname = '{}'
        """.format(
            schema
        )
        return [name for (name,) in self.db_engine.execute(sql)]

    def get_function_list_from_db(self, schema):
        sql = """
            select proname, oidvectortypes(proargtypes)
            from pg_proc
            inner join pg_namespace ns
                on (pg_proc.pronamespace = ns.oid)
            where ns.nspname = 'public'
        """
        return [row for row in self.db_engine.execute(sql)]

    def drop_schema(self, schema):
        for funcname, funcargs in self.get_function_list_from_db(schema):
            try:
                self.db_engine.execute(
                    'DROP FUNCTION "{}"."{}" ({}) CASCADE'.format(schema, funcname, funcargs)
                )
            except Exception as e:
                self.errors.append(str(e))

        for table in self.get_table_list_from_db(schema):
            try:
                self.db_engine.execute('DROP TABLE "{}"."{}" CASCADE'.format(schema, table))
            except Exception as e:
                self.errors.append(str(e))

        for seq in self.get_seq_list_from_db(schema):
            try:
                self.db_engine.execute('DROP SEQUENCE "{}"."{}" CASCADE'.format(schema, seq))
            except Exception as e:
                self.errors.append(str(e))

        for dbtype in self.get_type_list_from_db(schema):
            try:
                self.db_engine.execute('DROP TYPE "{}"."{}" CASCADE'.format(schema, dbtype))
            except Exception as e:
                self.errors.append(str(e))

    def drop_all(self, db_manager):
        for dialect_op in db_manager.all_bind_dialects():
            for schema in dialect_op.opt_schemas:
                self.drop_schema(schema)

    def restore_binary(self, restore_fpath):
        args = ['--no-owner', '-d', self.db_name]
        if self.jobs:
            args.extend(['-j', self.jobs])
        args.append(restore_fpath)
        self.pg_sub_run('pg_restore', args)

    def restore_sql(self, restore_fpath):
        args = ['-d', self.db_name, '--file', restore_fpath]
        self.pg_sub_run('psql', args)

    def run(self, *restore_fpaths):
        self.drop_all(self.db_manager)
        if not self.errors:
            for fpath in restore_fpaths:
                log.info(
                    'Restoring {2} to {0.host}:{0.port}/{1}'.format(
                        self.db_url, self.db_name, fpath
                    )
                )
                if fpath.endswith('.sql'):
                    self.restore_sql(fpath)
                elif fpath.endswith('.bak'):
                    self.restore_binary(fpath)
                elif os.path.isdir(fpath):
                    self.restore_date_dir(fpath)
                else:
                    raise Exception('Not sure how to restore path: {}'.format(fpath))
        return self.errors

    def restore_date_dir(self, dpath):
        """Restore a directory path which was created by our date backup."""
        bak_dpath = Path(dpath)
        db_exec = self.db_engine.execute
        conn = self.db_engine.raw_connection()
        cur = conn.cursor()

        def copy_from(table, fpath):
            with fpath.open('r', encoding='utf-8') as fo:
                cur.copy_from(fo, table)

        self.restore_sql(str(bak_dpath / '_schema.sql'))

        cur.execute('begin')

        # We have a circular dependency between races and events on events.current_race_id.  So
        # we need to defer checking on that constraint.
        db_exec('alter table events alter constraint events_current_race_id_fkey deferrable;')
        cur.execute('set constraints events_current_race_id_fkey deferred;')

        copy_from('tote_sources', bak_dpath / 'tote-sources.txt')
        copy_from('tote_source_runs', bak_dpath / 'tote-source-runs.txt')
        copy_from('events', bak_dpath / 'events.txt')
        copy_from('races', bak_dpath / 'races.txt')
        copy_from('race_wagers', bak_dpath / 'race-wagers.txt')
        cur.execute('commit')


class PostgresBackup(PostgresBase):
    def __init__(self, backup_dpath, db_engine=None):
        super().__init__(db_engine)
        self.backup_dpath = backup_dpath

    def pg_dump(self, *pg_dump_args, back_type=None, back_fpath=None):
        if back_fpath is None:
            assert back_type is not None
            fname = '{}-{}'.format(self.db_url.database, back_type)
            back_fpath = osp.join(self.backup_dpath, fname)
        args = list(pg_dump_args) + ['--file', back_fpath, self.db_url.database]
        log.info('Backing up to: {}'.format(back_fpath))
        self.pg_sub_run('pg_dump', args)

    def run(self, backup_type, date=None):
        if backup_type in ('both', 'sql'):
            self.pg_dump('-s', back_type='schema.sql')

            public_tables = self.get_table_list_from_db('public')
            if 'alembic_version' in public_tables:
                self.pg_dump('-t', 'alembic_version', back_type='alembic.sql')

        if backup_type in ('both', 'full'):
            self.pg_dump('--format', 'custom', '--blobs', back_type='full.bak')

        return self.errors

    def psql_copy_to(self, source, destination_fpath):
        psql_cmd = r"\copy {} to '{}' with encoding 'utf-8'".format(source, destination_fpath)
        args = ['-d', self.db_url.database, '-c', psql_cmd]
        self.pg_sub_run('psql', args)


def testing_db_restore(app):
    fpath_tpl = app.config.get('DB_RESTORE_SQL_FPATH')
    restore_fpaths = [fpath_tpl.format('schema')]
    alembic_fpath = fpath_tpl.format('alembic')
    if Path(alembic_fpath).exists():
        restore_fpaths.append(alembic_fpath)

    pgr = PostgresRestore()
    errors = pgr.run(*restore_fpaths)

    # Ugly exit if the restore fails for some reason
    assert not errors, errors

    # Run alembic migrations
    alembic_upgrade('head')


def migration_db_restore(migration_dpath):

    schema_fpath = str(migration_dpath / 'schema.sql')
    alembic_fpath = str(migration_dpath / 'alembic.sql')

    pgr = PostgresRestore()
    errors = pgr.run(schema_fpath, alembic_fpath)

    # Ugly exit if the restore fails for some reason
    assert not errors, errors


ReflectedDB = namedtuple('ReflectedDB', 'classes session')


@contextmanager
def reflect_db(conn):
    sa_session = sa_orm.Session(conn)

    class DeclarativeBase(MethodsMixin):
        session = sa_session

        @classproperty
        def query(cls):
            return cls.session.query(cls)

    DecBase = declarative_base(cls=DeclarativeBase)
    Base = automap_base(DecBase)
    # reflect the tables
    Base.prepare(conn, reflect=True)

    yield ReflectedDB(Base.classes, sa_session)
    sa_session.close()
