import os

from celery import Task as TaskBase
from celery.signals import setup_logging, worker_process_init
from keg.db import db

from ..app import AABC
# By using the name "celery" `celery worker` will find the instance.
from .app import celery_app as celery  # noqa


@setup_logging.connect
def add_handler(**kwargs):
    # This disables all Celery's logging.  We want Keg's logging configurations to apply.
    pass


# Config specific to WSGI workers
uwsgi_config = {
    # Don't log to stdout or uwsgi picks it up and that gets sent to syslog too resulting in double
    # the log volume with no benefit.
    'KEG_LOG_STREAM_ENABLED': os.environ.get('KEG_LOG_STREAM_ENABLED', False)
    == 'on'
}

# Assuming this module will only ever be called by `celery worker` and we therefore need to setup
# our application b/c it's not been done yet.
#
# You must set the AABC_CONFIG_PROFILE environment variable in
# order for this to work.  See project's readme for an example.
_app = AABC().init(config=uwsgi_config)


class ContextTask(TaskBase):
    """
    We need to wrap the execution of each Celery task in a Flask app context in order for
    flask.current_app and similiar to work.
    """

    # Abstract tells Celery not to register this task in the task registry.
    abstract = True

    def __call__(self, *args, **kwargs):
        with _app.app_context():
            return super().__call__(*args, **kwargs)


# It might seem like this assignment happens too late to be effective.  By the time this assignment
# takes place, the tasks in myapp.celery.tasks have already been setup.  However, it seems
# that Celery uses a proxy object for task registration which will defer the creation of the task
# classes until they are used.  From celery.app.base.Celery.task docstring:
#
#       App Binding: For custom apps the task decorator will return
#       a proxy object, so that the act of creating the task is not
#       performed until the task is used or the task registry is accessed.
#
#       If you're depending on binding to be deferred, then you must
#       not access any attributes on the returned object until the
#       application is fully set up (finalized).
celery.Task = ContextTask


@worker_process_init.connect
def prep_db_pool(**kwargs):
    """
    When Celery fork's the parent process, the db engine & connection pool is included in that.
    But, the db connections should not be shared across processes, so we tell the engine
    to dispose of all existing connections, which will cause new ones to be opend in the child
    processes as needed.
    More info: https://docs.sqlalchemy.org/en/latest/core/pooling.html#using-connection-pools-with-multiprocessing  # noqa
    """
    with _app.app_context():
        db.engine.dispose()
