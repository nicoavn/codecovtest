import flask
import flask_webtest as webtest
import pytest
from keg_auth.testing import AuthTestApp

from ..libs.testing import mock_patch
from ..model import entities as ents


# Scope needs to be class level b/c ViewTestBase clears out users in setup_class()
@pytest.fixture(scope='class')
def auth_client(perms=None):
    return AuthTestApp(flask.current_app, user=ents.User.testing_create(permissions=perms))


class TestPublic:
    @classmethod
    def setup_class(cls):
        # anonymous user
        cls.client = webtest.TestApp(flask.current_app)

    def test_ping(self):
        # This only tests the view layer, provided by Keg. Don't use this for cronitor.
        # Refs: https://github.com/level12/keg-app-cookiecutter/issues/130
        resp = self.client.get('/ping')
        assert resp.text == 'ABC ok'

    @mock_patch('ABC.views.public.ctasks')
    def test_health_check(self, m_ctasks):
        # Use this for cronitor.
        resp = self.client.get('/health-check')
        assert resp.text == 'ABC ok'
        m_ctasks.ping_url.apply_async.assert_called_once_with(('keep-celery-alive',), priority=10)

    def test_exception(self):
        # This tests the app exception route, not Kegs.
        # Refs: https://github.com/level12/keg-app-cookiecutter/issues/130
        with pytest.raises(Exception) as excinfo:
            self.client.get('/exception')
        assert str(excinfo.value) == 'Deliberate exception for testing purposes'

    def test_home(self, auth_client):
        resp = self.client.get('/')
        assert resp.pyquery('main p').text() == 'You need to login.'

        resp = auth_client.get('/')
        assert resp.pyquery('main p').text() == 'This is the home page. :)'
