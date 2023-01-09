import click

from ..app import AABC
from ..libs import db as lib_db


@AABC.cli.group()
def db():
    pass


@db.command()
@click.argument('restore_fpaths', type=click.Path(exists=True), nargs=-1)
@click.option('--db-name')
@click.option('--jobs', '-j', default=None, type=int)
def restore(restore_fpaths, db_name, jobs):
    jobs = jobs if jobs is None else str(jobs)
    pgr = lib_db.PostgresRestore(db_name, jobs=jobs)
    errors = pgr.run(*restore_fpaths)
    if errors:
        [print(e) for e in errors]
    else:
        print('restore finished')


@db.command()
@click.argument('backup-type', type=click.Choice(['full', 'sql', 'both']))
@click.option('--save-to', type=click.Path(exists=True), default='/tmp/')
def backup(save_to, backup_type):
    pgb = lib_db.PostgresBackup(save_to)
    errors = pgb.run(backup_type)

    if errors:
        [print(e) for e in errors]
    else:
        print('backup finished')
