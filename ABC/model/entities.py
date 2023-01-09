import logging

import keg_auth
import sqlalchemy as sa
from keg.db import db
from sqlalchemy.dialects.postgresql import JSONB

from ..extensions import auth_entity_registry
from ..libs.model import EntityMixin

log = logging.getLogger(__name__)

# Default cascade setting for parent/child relationships.  Should get set on parent side.
# Docs: https://l12.io/sa-parent-child-relationship-config
_rel_cascade = 'all, delete-orphan'


@auth_entity_registry.register_user
class User(keg_auth.UserEmailMixin, keg_auth.UserMixin, EntityMixin, db.Model):
    """Make sure EntityMixin is after UserMixin or testing_create() is wrong."""

    __tablename__ = 'auth_users'

    name = sa.Column(sa.Unicode(250), nullable=False)
    settings = sa.Column(JSONB)


@auth_entity_registry.register_permission
class Permission(keg_auth.PermissionMixin, EntityMixin, db.Model):
    __tablename__ = 'auth_permissions'

    def __repr__(self):
        return '<Permission id={} token={}>'.format(self.id, self.token)


@auth_entity_registry.register_bundle
class Bundle(keg_auth.BundleMixin, EntityMixin, db.Model):
    __tablename__ = 'auth_bundles'


@auth_entity_registry.register_group
class Group(keg_auth.GroupMixin, EntityMixin, db.Model):
    __tablename__ = 'auth_groups'


@auth_entity_registry.register_attempt
class Attempt(keg_auth.AttemptMixin, EntityMixin, db.Model):
    __tablename__ = 'auth_attempts'
