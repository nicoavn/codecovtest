import logging

import flask
from keg.db import db

from ..celery import tasks as ctasks
from ..libs.views import BaseView

log = logging.getLogger(__name__)
public_bp = flask.Blueprint(
    'public',
    __name__,
)


class HealthCheck(BaseView):
    """An endpoint our monitoring service can watch that, unlike Keg's /ping, will also
    test connectivity to the DB and ping Celery Alive URL before returning an "ok" message.
    """

    blueprint = public_bp

    def get(self):
        # We are happy if this doesn't throw an exception.  Nothing to test b/c we aren't sure
        # there will be a user record.
        db.engine.execute('select id from auth_users limit 1').fetchall()

        # Log aggregator (e.g. Loggly) can alert on this as a "heartbeat" for the app assuming
        # something like Cronitor is hitting this URL repeatedly to monitor uptime.
        log.info('ping-db ok')

        alive_url = flask.current_app.config['CELERY_ALIVE_URL']

        ctasks.ping_url.apply_async((alive_url,), priority=10)

        return '{} ok'.format(flask.current_app.name)


@public_bp.route('/exception')
def exception_test():
    raise Exception('Deliberate exception for testing purposes')


class Home(BaseView):
    # Template name by convention, see: templates/public/home.html
    blueprint = public_bp
    url = '/'

    def get(self):
        return
        # You may want this eventually:
        # from flask_login import current_user
        # if not current_user.is_authenticated:
        #    return flask.redirect(flask.url_for('auth.login'))
