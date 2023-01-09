import contextlib
from unittest import mock

import blazeutils
import flask
import keg_auth.testing
import sqlalchemy
import wrapt
from flask_wtf.csrf import generate_csrf
from keg import signals
from sqlalchemy.dialects import postgresql as sa_postgresql
from webgrid.testing import compiler_instance_factory

from ..model import entities as ents


def inrequest(*req_args, **req_kwargs):
    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        with flask.current_app.test_request_context(*req_args, **req_kwargs):
            return wrapped(*args, **kwargs)

    return wrapper


@contextlib.contextmanager
def app_config_cli(**kwargs):
    """
    Set config values on any apps instantiated while the context manager is active.
    This is intended to be used with cli tests where the `current_app` in the test will be
    different from the `current_app` when the CLI command is invoked, making it very difficult
    to dynamically set app config variables using mock.patch.dict like we normally would.
    Example::
    class TestCLI(CLIBase):
        app_cls = AABC
        def test_it(self):
            with testing.app_config_cli(FOO_NAME='Bar'):
                result = self.invoke('echo-foo-name')
            assert 'Bar' in result.output
    """

    @signals.config_complete.connect
    def set_config(app):
        app.config.update(kwargs)

    yield


@contextlib.contextmanager
def app_config(**kwargs):
    """Just a shortcut for mock.patch.dict...
    def test_it(self):
        with testing.app_config(FOO_NAME='Bar'):
            assert flask.current_app.config['FOO_NAME'] == 'Bar'
    """
    with mock.patch.dict(flask.current_app.config, **kwargs) as mocked_config:
        yield mocked_config


def mock_patch_obj(*args, **kwargs):
    kwargs.setdefault('autospec', True)
    kwargs.setdefault('spec_set', True)
    return mock.patch.object(*args, **kwargs)


def mock_patch(*args, **kwargs):
    kwargs.setdefault('autospec', True)
    kwargs.setdefault('spec_set', True)
    return mock.patch(*args, **kwargs)


def query_to_str(statement, bind=None):
    """
    returns a string of a sqlalchemy.orm.Query with parameters bound
    WARNING: this is dangerous and ONLY for testing, executing the results
    of this function can result in an SQL Injection attack.
    """
    if isinstance(statement, sqlalchemy.orm.Query):
        if bind is None:
            bind = statement.session.get_bind()
        statement = statement.statement
    elif bind is None:
        bind = statement.bind

    if bind is None:
        raise Exception(
            'bind param (engine or connection object) required when using with an'
            ' unbound statement'
        )

    dialect = bind.dialect
    compiler = statement._compiler(dialect)
    literal_compiler = compiler_instance_factory(compiler, dialect, statement)
    return 'TESTING ONLY BIND: ' + literal_compiler.process(statement)


def print_sa(statement):
    '''Print an SA statment compiled as it will actually look when sent to postgres.  A lot of the
    time, this is no different from what you'd get with print(statement), but it can matter
    for Postgres specific syntax like their `distinct on (...)`.
    SA core statements get passed in directly: print_sa(select(...))
    SA ORM queries should send in the statement: print_sa(ents.SomeThing.query.statement)
    '''
    print(statement.compile(dialect=sa_postgresql.dialect()))


def user_client(user=None, permissions=None, is_active=True):
    permission_ent = flask.current_app.auth_manager.entity_registry.permission_cls

    if user is None:
        # ensure all of the tokens exists
        defined_perms = set(
            blazeutils.tolist(perm)[0] for perm in flask.current_app.auth_manager.permissions
        )
        for perm in blazeutils.tolist(permissions):
            if perm not in defined_perms:
                raise Exception('permission {} not specified in the auth manager'.format(perm))
            permission_ent.testing_create(token=perm)

        user = ents.User.testing_create(is_active=is_active, permissions=permissions or ())
    test_app = AuthTestApp(flask.current_app, user=user)
    test_app.__user__ = user
    return test_app


class AuthTestApp(keg_auth.testing.AuthTestApp):
    """
    Adds features to help with CSRF validation.
    """

    def __init__(self, app, **kwargs):
        self._csrf_token = None
        self._add_csrf = kwargs.pop('add_csrf', False)

        super().__init__(app, **kwargs)

    def _gen_csrf(self):
        if not self._csrf_token:
            with self.app.test_request_context():
                self._csrf_token = generate_csrf()
                raw_token = flask.session['csrf_token']

            with self.session_transaction() as sess:
                sess['csrf_token'] = raw_token

        return self._csrf_token

    def post(self, *args, **kwargs):
        if kwargs.pop('add_csrf', self._add_csrf):
            kwargs.setdefault('headers', {})
            kwargs['headers']['X-CSRF-Token'] = self._gen_csrf()

        return super().post(*args, **kwargs)
