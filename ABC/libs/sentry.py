import keg_elements.sentry as ke_sentry
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration


class SentryEventFilter(ke_sentry.SentryEventFilter):
    sanitized_config_keys = [
        *ke_sentry.SentryEventFilter.sanitized_config_keys,
        'DEVELOPER_PASSWORD',
    ]


class Sentry:
    def init_app(self, app):
        # `FlaskIntegration` and `LoggingIntegration` are already added by keg-elements
        integrations = [
            CeleryIntegration(),
            SqlalchemyIntegration(),
        ]

        ke_sentry.install_sentry(app, integrations, event_filter=SentryEventFilter())
