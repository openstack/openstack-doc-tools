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


HOOKS = {'keystone.common.config': keystone_config}
