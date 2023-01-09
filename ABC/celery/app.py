import logging

from celery import Celery
from celery.signals import task_postrun
from keg.db import db
from keg.signals import app_ready

log = logging.getLogger(__name__)


def on_task_failure(task, exc, task_id, args, kwargs, einfo):
    """
    Log any task failures.  We will also get email notifications which is handled directly by
    celery and setup in the workers module.
    """
    message = 'Task {} failed w/ args: {}, {}\n{}'
    log.error(message.format(task.name, args, kwargs, einfo.traceback))


@task_postrun.connect
def on_task_postrun(task_id, task, args, kwargs, retval, state, **extra):
    # Remove the db session to avoid memory problems and to clear out any failed DB
    # transactions so future tasks in this process don't get hung up.
    db.session.remove()


@app_ready.connect
def configure(keg_app):
    celery_config = keg_app.config['CELERY'].copy()

    # Use a custom failure handler so we can get logs of any failures.
    celery_config['task_annotations'] = {'*': {'on_failure': on_task_failure}}

    # Most of the celery configuration should happen in the normal settings files for this app.
    celery_app.conf.update(celery_config)


celery_app = Celery(
    'ABC',
    include=['ABC.celery.tasks']
)

# Quickly fail if RabbitMQ can't be reached so tests/scripts don't hang.
celery_app.conf['broker_transport_options'] = {"max_retries": 1}
