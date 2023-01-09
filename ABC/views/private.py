import flask
from keg_auth import requires_user


@requires_user()
class ProtectedBlueprint(flask.Blueprint):
    pass


private_bp = ProtectedBlueprint(
    'private',
    __name__,
)
