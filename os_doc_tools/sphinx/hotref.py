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

"""Sphinx extension to create references to the HOT reference resources.

    This extension provides some inline markup to automatically generate links
    to the OpenStack HOT reference resources.

    Usage examples:

        The :hotref:`OS::Nova::Server` resource creates a new instance.
        The :hotref:os:`OS::Nova:Server` resource also.
        The :hotref:cfn:`AWS::CloudFormation::WaitCondition` is an AWS
        resource.

    To use this extension, add 'os_doc_tools.sphinx.hotref' in the `extensions`
    list of your conf.py file."""

from docutils import nodes
from docutils import utils


def build_ref_node(prefix, rawtext, app, resource, options):
    link = resource.replace(':', '_')
    base = app.config.hotref_base_url
    ref = "%(base)s/%(prefix)s_%(name)s.html" % {'base': base,
                                                 'prefix': prefix,
                                                 'name': link}
    literal = nodes.literal('')
    ref_node = nodes.reference(rawtext, utils.unescape(resource),
                               refuri=ref, **options)
    literal.append(ref_node)
    return literal


def hotref_os_role(name, rawtext, text, lineno, inliner, options={},
                   content=[]):
    app = inliner.document.settings.env.app
    node = build_ref_node('openstack', rawtext, app, text, options)
    return [node], []


def hotref_cfn_role(name, rawtext, text, lineno, inliner, options={},
                    content=[]):
    app = inliner.document.settings.env.app
    node = build_ref_node('cfn', rawtext, app, text, options)
    return [node], []


def setup(app):
    app.add_role('hotref', hotref_os_role)
    app.add_role('hotref:os', hotref_os_role)
    app.add_role('hotref:cfn', hotref_cfn_role)
    app.add_config_value('hotref_base_url',
                         'http://docs.openstack.org/hot-reference/content',
                         'env')
