#
# A collection of shared functions for managing help flag mapping files.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
"""Hooks to handle configuration options not handled on module import or with a
call to _register_runtime_opts(). The HOOKS dict associate hook functions with
a module path."""


def keystone_config():
    from keystone.common import config

    config.configure()


def glance_store_config():
    try:
        import glance_store
        from oslo_config import cfg

        glance_store.backend.register_opts(cfg.CONF)
    except ImportError:
        # glance_store is not available before Juno
        pass


def neutron_misc():
    try:
        # These imports are needed for kilo only
        import bsnstacklib.plugins.bigswitch.config
        import networking_cisco.plugins.cisco.cfg_agent.device_status  # noqa
        import networking_l2gw.services.l2gateway.common.config as l2gw
        import networking_vsphere.common.config
        from oslo_config import cfg
        import vmware_nsx.neutron.plugins.vmware.common.config  # noqa

        bsnstacklib.plugins.bigswitch.config.register_config()
        networking_vsphere.common.config.register_options()
        l2gw.register_l2gw_opts_helper()
        l2gw.register_ovsdb_opts_helper(cfg.CONF)
    except Exception:
        pass


def nova_spice():
    import os
    # nova.cmd.__init__ before kilo requires to be imported before eventlet is.
    # Since we can't make sure of that, we define this envvar to let nova know
    # that the import is OK (see nova/cmd/__init__.py)
    os.environ['EVENTLET_NO_GREENDNS'] = 'yes'
    import nova.cmd.spicehtml5proxy  # noqa


HOOKS = {'keystone.common.config': keystone_config,
         'glance.common.config': glance_store_config,
         'neutron': neutron_misc,
         'nova.spice': nova_spice}
