import keg
import pytest

from ..libs import sentry


class TestSentryEventFilter:
    @pytest.mark.parametrize(
        'key',
        [
            'token',
            'password',
            'secret',
            'passwd',
            'authorization',
            'sentry_dsn',
            'xsrf',
            'some_key',
        ],
    )
    def test_sanitize(self, key):
        event = {
            'exception': {
                'stacktrace': {
                    'frames': [
                        {'module': 'foo.bar', 'vars': {'notfiltered': 'foo', key: 'abc'}},
                    ]
                },
            }
        }
        filtered = sentry.SentryEventFilter().before_send(event, {})
        assert filtered == {
            'exception': {
                'stacktrace': {
                    'frames': [
                        {
                            'module': 'foo.bar',
                            'vars': {
                                'notfiltered': 'foo',
                                key: '<Filtered str>',
                            },
                        },
                    ]
                },
            }
        }

    @pytest.mark.parametrize(
        'key',
        [
            'SECRET_KEY',
            'DEVELOPER_PASSWORD',
        ],
    )
    def test_sanitize_config_value(self, key, monkeypatch):
        monkeypatch.setitem(keg.current_app.config, key, 'filtered-value')
        event = {
            'exception': {
                'stacktrace': {
                    'frames': [
                        {
                            'module': 'foo.bar',
                            'vars': {'notfiltered': 'foo', 'filtered': '**filtered-value**'},
                        },
                    ]
                },
            }
        }
        filtered = sentry.SentryEventFilter().before_send(event, {})
        assert filtered == {
            'exception': {
                'stacktrace': {
                    'frames': [
                        {
                            'module': 'foo.bar',
                            'vars': {
                                'notfiltered': 'foo',
                                'filtered': '**<Filtered str>**',
                            },
                        },
                    ]
                },
            }
        }
