from ABC.celery.config import celery_config

DEFAULT_PROFILE = 'DevProfile'


class DevProfile:
    # Secret key for Flask -- CHANGE THIS!
    SECRET_KEY = 'abc123'

    # Examples:
    #   Socket based, no pass: postgresql://USER@:5433/abc
    #   TCP/IP based & matches docker-compose: postgresql://postgres@127.0.0.1:12432/abc
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres@localhost:12432/abc'

    # These are used for creating an initial developer user following database init
    DEVELOPER_NAME = 'Alvin Duran'
    DEVELOPER_EMAIL = 'alvin.durang@level12.io'
    DEVELOPER_PASSWORD = '1234qwer'

    MAIL_DEFAULT_SENDER = 'alvin.durang@level12.io'
    MAIL_SUPPRESS_SEND = True

    KEG_LOG_SYSLOG_ENABLED = False

    # Needed by at least KegAuth for sending emails from the command line
    SERVER_NAME = 'localhost:5000'

    CELERY = celery_config(broker_url='amqp://guest@localhost:12672//')


class TestProfile:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres@localhost:12432/abc-tests'

    # Make tests faster
    PASSLIB_CRYPTCONTEXT_KWARGS = dict(schemes=['plaintext'])

    # Mail related tests need to have this set, even though actual email is not generated.
    MAIL_DEFAULT_SENDER = 'alvin.durang@level12.io'

    CELERY = celery_config(broker_url='amqp://guest@localhost:12672//', queue_name='__tests__')

    # When using `py.test --db-restore ...` this setting tells us what the backup files names look
    # like.  See ABC.libs.db.testing_db_restore() for more details.
    # Use ./ansible/db-backup.yaml to create these files and view the readme for more information.
    # DB_RESTORE_SQL_FPATH = '/tmp/abc-prod-{}.sql'
    # DB_RESTORE_SQL_FPATH = '/tmp/abc-beta-{}.sql'
    DB_RESTORE_SQL_FPATH = '/tmp/test-{}.sql'
