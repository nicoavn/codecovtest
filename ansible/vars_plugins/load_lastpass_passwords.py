"""
References for creating a vars plugin:

* https://docs.ansible.com/ansible/latest/plugins/vars.html
* https://docs.ansible.com/ansible/latest/dev_guide/developing_plugins.html#vars-plugins
* https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/vars/host_group_vars.py

"""
# Next two lines came from host_group_vars.py example
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pathlib

from ansible.errors import AnsibleError
from ansible.plugins.vars import BaseVarsPlugin

# Something like the following should get you what you need here:
# pip install -e ~/projects/level12-cli-src/[lastpass]
from level12.libs.ansible import lastpass_lookup

map_secrets_fpath = pathlib.Path(__file__).parent.parent.joinpath('files', 'map_secrets.py')
map_secrets_globals = {}
with map_secrets_fpath.open() as fo:
    exec(fo.read(), map_secrets_globals)

# This has to be ran outside `get_vars()` below.  If you don't, then Ansible just exits early.
# I suspect it has something to do with lastpass_lookup() executing a lpass subprocess.  But, this
# is good b/c it caches the variables for us.
lp_result = lastpass_lookup(
    map_secrets_globals['varmap'], map_secrets_globals['lastpass_folder'], jsonify=True
)


class VarsModule(BaseVarsPlugin):
    def get_vars(self, loader, path, entities, cache=True):
        if lp_result.exc:
            msg = 'unhandled exception when running lookup-passwords'
            raise AnsibleError('{}\n{}'.format(msg, lp_result.exc))

        # A simple error message that just needs to be shown to the user.  Use AnsibleError
        # so that the message is displayed nicely and the playbooks stop running.
        if lp_result.error:
            raise AnsibleError(lp_result.error)

        return lp_result.vars
