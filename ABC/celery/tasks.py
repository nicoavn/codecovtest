import logging

import requests

from .app import celery_app as app

log = logging.getLogger(__name__)


@app.task(bind=True, max_retries=10)
def ping_url(self, url, retry_wait_secs=1):
    log.info('pinging URL: %s', url)

    try:
        requests.get(url, timeout=10)
    except requests.RequestException:
        log.exception('ping_url() encountered an exception')
        raise self.retry(countdown=retry_wait_secs)


@app.task
def say(msg):
    log.info(f'say: {msg}')
