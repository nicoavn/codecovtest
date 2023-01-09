from time import sleep
from unittest import mock

from keg.testing import CLIBase

from ..celery import tasks
from ..celery.testing import task_tracker
from ..model import entities as ents


class TestCLI(CLIBase):
    def setup(self):
        ents.User.delete_cascaded()

    def test_add_user(self):
        self.invoke('auth', 'create-user', 'foo@bar.com', 'Foo Bar')
        assert ents.User.query.count() == 1
        assert ents.User.query.filter_by(is_superuser=True).count() == 0

    def test_add_superuser(self):
        self.invoke('auth', 'create-user', '--as-superuser', 'foo@bar.com', 'Foo Bar')
        assert ents.User.query.count() == 1
        assert ents.User.query.filter_by(is_superuser=True).count() == 1


class TestCelerySetup:
    def setup(self):
        task_tracker.reset()

    @mock.patch.object(tasks, 'requests', autospec=True, spec_set=True)
    @mock.patch('ABC.celery.app.db', autospec=True, spec_set=True)
    def test_removed_ok(self, m_db, m_requests, celery_session_worker):
        """The DB session needs to be removed when every task is finished."""

        tasks.ping_url.delay('foo')

        # Wait for the task to complete in a different thread.
        task_tracker.wait_for('ABC.celery.tasks.ping_url')
        # Cleanup is sometimes not complete at this point, need to sleep a minimal amount more
        sleep(0.3)

        m_db.session.remove.assert_called_once_with()


class TestDBCli(CLIBase):
    @mock.patch('ABC.cli.db.lib_db.PostgresBackup', autospec=True, spec_set=True)
    def test_backup(self, m_PostgresBackup):
        # set "errors" to nothing
        m_PostgresBackup.return_value.run.return_value = []
        result = self.invoke('db', 'backup', 'sql')
        assert 'backup finished\n' == result.output

    @mock.patch('ABC.cli.db.lib_db.PostgresRestore', autospec=True, spec_set=True)
    def test_restore(self, PostgresRestore):
        # set "errors" to nothing
        PostgresRestore.return_value.run.return_value = []
        # The restore doesn't work b/c of the mock, but we have to feed it a path that exists.
        result = self.invoke('db', 'restore', '/tmp')
        assert 'restore finished\n' == result.output
