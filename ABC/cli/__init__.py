import logging

from ..app import AABC

# These imports are to get the cli sub-modules loaded.
from . import celery  # noqa
from . import db  # noqa

log = logging.getLogger(__name__)


def cli_entry():
    AABC.cli.main()


if __name__ == '__main__':
    cli_entry()
