.. default-role:: code

ABC's Readme
######################################

.. image:: https://circleci.com/gh/nicoavn/codecovtest.svg?&style=shield&circle-token=abc
    :target: https://circleci.com/gh/nicoavn/codecovtest

.. image:: https://codecov.io/github/nicoavn/codecovtest/coverage.svg?branch=master&token=abc
    :target: https://codecov.io/github/nicoavn/codecovtest?branch=master

Project Setup Checklist
=======================

* `tox`
* setup git hooks via pre-commit
* create project on

  * GitHub
  * Appveyor?
  * Sentry

* Setup Slack integrations for

  * CircleCI
  * Appveyor
  * Sentry

* Build requirements files::

    cd requirements
    make

* Git init, commit, push
* Verify

  * CI builds pass
  * Coverage is pushed
  * Failed CI builds show up in a Slack channel

* Update this readme

What's In This App
=======================

The application produced by keg-app-cookiecutter is intended to integrate the various tools and
practices needed for Keg apps. The readme sections below have specifics for several areas that
will be applicable to most projects and should likely be retained. This section, and the checklist
above, can be removed in favor of project-specific information.

Tools/concepts included in this app:

* Environment setup and usage with pip-tools
* Configuration and helpful defaults
* Docker setup for dependency services
* Basic app, model, views
* Keg-Auth integration

  * User/group/permission/bundle model
  * Email notifications
  * Use of view test helpers to efficiently set up an authenticated client

* Webgrid setup
* Celery setup and usage for background process workers
* Template/navigation

  * Uses Keg-Auth navigation helpers

  * Limits available menu items to those that pass basic authorization tests
  * Auto-expands menu to the item matching the current view, and highlights it

* Example views showing public/private authentication requirements and authorization
* Migrations with alembic

  * Support for separation of schema and data migrations

* Deployment through ansible

  * LastPass CLI usage for gathering deployment secrets

* CI configuration
* Monitoring needs for app health and celery
* Sentry setup for exception handling/reporting
* Accepted linting standards

Secrets
=========

All sensitive information should be stored in LastPass: Shared-NICOAVN-Z

Secrets are pulled in from from LastPass using the `lpass cli`_ binary for both development usage
and ansible.  Make sure you have the binary installed to a location on your PATH.  The first time
you use the lpass binary, it will pop up a dialogue asking for you LastPass password.

.. _lpass cli: https://github.com/lastpass/lastpass-cli

Quickstart
==========

#. Clone the repo

#. `docker-compose up -d` or you will have to have the same services available without Docker.

#. Copy the file `abc-config-example.py` at the root of this project to
   `abc-config.py`. Adjust settings as needed for your local dev environment.

#. Copy the file `.flaskenv-example` at the root of this project to `.flaskenv`. Adjust settings as
   needed for your local dev environment.

#. Run `tox` and verify the tests pass.  Read the tox file to learn how this project sets up
   dependencies and runs tests.

#. Create and activate a virtualenv with the version of Python tox is testing with.

#. We use pip-tools to manage Python dependencies in this project.  Add dependencies to the
   list in `requirements/common.in`, run `make` in the `requirements` folder, and `pip-sync`
   the result.

#. You will have to install the project separately with `pip install -e .`

#. Set up pre-commit by running `pre-commit install`. Change when hooks run by passing the `--hook-type` flag
   (see https://pre-commit.com/#pre-commit-during-push).

#. Set up the database tables with `ABC develop db init`

#. Run the app with `supervisord` (inspect supervisord.conf for more info).

Celery
=================

The celery worker can be run with::

    ./scripts/celery-worker

View your queues and stuff using flower (`pip install flower`)::

    celery flower --app ABC.celery.worker

Purging the queues::

    ./scripts/celery-purge

Deploy
==================

All commands are given for beta, change to `-l prod` for production.

A user with sudo permissions on the server must run the provision::

    ansible-playbook -l beta provision.yaml

You can verify the provision by browsing to (something like)::

    https://yourapp-beta.level12.biz

Assuming that is successful, you should then deploy::

    # For the first run, create the database from the model
    ansible-playbook -l beta deploy.yaml --extra-vars=first_run=true

    # Subsequent deploys will use Alembic migrations
    ansible-playbook -l beta deploy.yaml

You can verify the deploy by:

* Browsing to: https://yourapp-beta.level12.biz/health-check
* Browsing to: https://yourapp-beta.level12.biz/exception-test

  * Verify this shows up in Sentry

* Verify the app's logging messages through Celery, which cron should be running once a minute.
  You can run manually with: `ABC log` and `ABC celery ping`.

  * Look on the server in ~/syslogs/app.log for the app's log messages
  * Look at logzio, the messages should have shipped there as well through rsyslog

* Setup health-check and Celery alive monitors on the Cronitor dashboard. This
  ensures both that the uwsgi service is alive and Celery is running.

  * Example monitors are on Cronitor under KegDemo


Database Backup, Restore, and Migration Tests
---------------------------------------------

Backups
~~~~~~~

::

    # Schema and alembic table only
    .../ansible$ ansible-playbook -l prod db-backup.yaml -t sql

    # Complete backup with data
    .../ansible$ ansible-playbook -l prod db-backup.yaml -t full

    # Find the backups on your local machine
    $ ls -lh /tmp/abc-*

Files will be generated on the remote server, downloaded to `/tmp`, and then deleted from the
server.


Restore
~~~~~~~

::

    # Restore SQL files - schema, alembic table if it exists, but no data
    $ abc db-restore /tmp/abc-*.sql
    INFO - abc.libs.db - Restoring /tmp/abc-schema.sql to None:5433/abc
    restore finished

    # Or, full restore with data
    $ abc db-restore /tmp/abc-full.bak
    INFO - abc.libs.db - Restoring /tmp/abc-full.bak to None:5433/abc
    restore finished


Migration Tests
~~~~~~~~~~~~~~~

By default, when tests run, the db schema is cleared out at the beginning of the test run and
we use SQLAlchemy to create all DB objects before starting the tests.  This is convenient for most
development tests, but won't catch errors in DB migrations because they aren't being applied in
the testing process.

So, we would like a way to run tests on top of a DB that has been prepared by restoring & applying
Alembic migrations.  We have some pytest integration which does most of that work for us::

    $ py.test --db-restore ABC

That will:

1. Restore the tests database using the files specified by DB_RESTORE_SQL_FPATH (see config example).
2. Run `alembic upgrade head` for the tests database.
3. Skip the DB init Keg would normally do during testing (since we get our schema from the restore + migration).
4. py.test continues as it otherwise would.
