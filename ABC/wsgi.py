from .app import AABC

# Config specific to WSGI workers
uwsgi_config = {
    # Don't log to stdout or uwsgi picks it up and that gets sent to syslog too resulting in double
    # the log volume with no benefit.
    'KEG_LOG_STREAM_ENABLED': False
}
application = AABC().init(config=uwsgi_config)
