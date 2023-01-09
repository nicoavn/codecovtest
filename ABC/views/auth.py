import logging

from keg_auth import make_blueprint
from keg_auth.forms import user_form as user_form_base
from keg_auth.views import User as UserBase

from ..extensions import auth_manager

log = logging.getLogger(__name__)


def user_form(config, allow_superuser, endpoint, fields=['name', 'is_enabled']):
    return user_form_base(config, allow_superuser, endpoint, fields=fields)


class User(UserBase):
    # need to make this a static method so it isn't bound on the view instance
    form_cls = staticmethod(user_form)


# This blueprint is for keg-auth's views (Login, user management, etc.)
auth_bp = make_blueprint(__name__, auth_manager, user_crud_cls=User)
