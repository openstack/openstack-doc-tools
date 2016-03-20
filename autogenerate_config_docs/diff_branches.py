#!/usr/bin/env python
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
# A collection of tools for working with flags from OpenStack
# packages and documentation.
#
# For an example of usage, run this program with the -h switch.
#
import argparse
import os
import pickle
import subprocess
import sys

import jinja2


PROJECTS = ['aodh', 'ceilometer', 'cinder', 'glance', 'heat', 'ironic',
            'keystone', 'manila', 'neutron', 'nova', 'sahara', 'swift',
            'trove']
MASTER_RELEASE = 'Mitaka'
CODENAME_TITLE = {'aodh': 'Alarming',
                  'ceilometer': 'Telemetry',
                  'cinder': 'Block Storage',
                  'glance': 'Image service',
                  'heat': 'Orchestration',
                  'ironic': 'Bare Metal service',
                  'keystone': 'Identity service',
                  'manila': 'Shared File Systems service',
                  'neutron': 'Networking',
                  'nova': 'Compute',
                  'sahara': 'Data Processing service',
                  'swift': 'Object Storage service',
                  'trove': 'Database service'}


def setup_venv(projects, branch, novenvupdate):
    """Setup a virtual environment for `branch`."""
    dirname = os.path.join('venv', branch.replace('/', '_'))
    if novenvupdate and os.path.exists(dirname):
        return
    if not os.path.exists('venv'):
        os.mkdir('venv')
    args = ["./autohelp-wrapper", "-b", branch, "-e", dirname, "setup"]
    args.extend(projects)
    if subprocess.call(args) != 0:
        print("Impossible to create the %s environment." % branch)
        sys.exit(1)


def _get_packages(project, branch):
    release = branch if '/' not in branch else branch.split('/')[1]
    packages = [project]
    try:
        with open('extra_repos/%s-%s.txt' % (project, release)) as f:
            packages.extend([p.strip() for p in f])
    except IOError:
        pass

    return packages


def get_options(project, branch):
    """Get the list of known options for a project."""
    print("Working on %(project)s (%(branch)s)" % {'project': project,
                                                   'branch': branch})
    # And run autohelp script to get a serialized dict of the discovered
    # options
    dirname = os.path.join('venv', branch.replace('/', '_'))
    args = ["./autohelp-wrapper", "-q", "-b", branch, "-e", dirname,
            "dump", project]

    path = os.environ.get("PATH")
    bin_path = os.path.abspath(os.path.join(dirname, "bin"))
    path = "%s:%s" % (bin_path, path)
    serialized = subprocess.check_output(args,
                                         env={'VIRTUAL_ENV': dirname,
                                              'PATH': path})
    ret = pickle.loads(serialized)
    return ret


def _cmpopts(x, y):
    """Compare to option names.

    The options can be of 2 forms: option_name or group/option_name. Options
    without a group always comes first. Options are sorted alphabetically
    inside a group.
    """
    if '/' in x and '/' in y:
        prex = x[:x.find('/')]
        prey = y[:y.find('/')]
        if prex != prey:
            return cmp(prex, prey)
        return cmp(x, y)
    elif '/' in x:
        return 1
    elif '/' in y:
        return -1
    else:
        return cmp(x, y)


def diff(old_list, new_list):
    """Compare the old and new lists of options."""
    new_opts = []
    new_defaults = []
    deprecated_opts = []
    for name, (group, option) in new_list.items():
        # Find the new options
        if name not in old_list.viewkeys():
            new_opts.append(name)

        # Find the options for which the default value has changed
        elif option['default'] != old_list[name][1]['default']:
            new_defaults.append(name)

        # Find options that have been deprecated in the new release.
        # If an option name is a key in the old_list dict, it means that it
        # wasn't deprecated.

        # Some options are deprecated, but not replaced with a new option.
        # These options usually contain 'DEPRECATED' in their help string.
        if 'DEPRECATED' in option['help']:
            deprecated_opts.append((name, None))

        for deprecated in option['deprecated_opts']:
            # deprecated_opts is a list which always holds at least 1 invalid
            # dict. Forget it.
            if deprecated['name'] is None:
                continue

            if deprecated['group'] in [None, 'DEFAULT']:
                full_name = deprecated['name']
            else:
                full_name = deprecated['group'] + '/' + deprecated['name']

            if full_name in old_list.viewkeys():
                deprecated_opts.append((full_name, name))

    return new_opts, new_defaults, deprecated_opts


def format_option_name(name):
    """Return a formatted string for the option path."""
    if name is None:
        return "None"

    try:
        section, name = name.split('/')
    except ValueError:
        # name without a section ('log_dir')
        return "[DEFAULT] %s" % name

    try:
        # If we're dealing with swift, we'll have a filename to extract
        # ('proxy-server|filter:tempurl/use')
        filename, section = section.split('|')
        return "%s.conf: [%s] %s" % (filename, section, name)
    except ValueError:
        # section but no filename ('database/connection')
        return "[%s] %s" % (section, name)


def release_from_branch(branch):
    if branch == 'master':
        return MASTER_RELEASE
    else:
        return branch.replace('stable/', '').title()


def get_env(project, new_branch, old_list, new_list):
    """Generate the jinja2 environment for the defined branch and project."""
    new_opts, new_defaults, deprecated_opts = diff(old_list, new_list)
    release = release_from_branch(new_branch)

    env = {
        'release': release,
        'project': project,
        'codename': CODENAME_TITLE[project],
        'new_opts': [],
        'new_defaults': [],
        'deprecated_opts': []
    }

    # New options
    if new_opts:
        for name in sorted(new_opts, _cmpopts):
            opt = new_list[name][1]
            name = format_option_name(name)
            helptext = opt['help'].strip().replace('\n', ' ')
            helptext = ' '.join(helptext.split())
            cells = (("%(name)s = %(default)s" %
                      {'name': name,
                       'default': opt['default']}).strip(),
                     "(%(type)s) %(help)s" % {'type': opt['type'],
                                              'help': helptext})
            env['new_opts'].append(cells)

    # New defaults
    if new_defaults:
        for name in sorted(new_defaults, _cmpopts):
            old_default = old_list[name][1]['default']
            new_default = new_list[name][1]['default']
            if isinstance(old_default, list):
                old_default = ", ".join(old_default)
            if isinstance(new_default, list):
                new_default = ", ".join(new_default)
            name = format_option_name(name)
            cells = (name, old_default, new_default)
            env['new_defaults'].append(cells)

    # Deprecated options
    if deprecated_opts:
        for deprecated, new in sorted(deprecated_opts, cmp=_cmpopts,
                                      key=lambda tup: tup[0]):
            deprecated = format_option_name(deprecated)
            new = format_option_name(new)
            env['deprecated_opts'].append((deprecated, new))

    return env


def main():
    parser = argparse.ArgumentParser(
        description='Generate a summary of configuration option changes.',
        usage='%(prog)s [options] <old_branch> <new_branch> [projects]')
    parser.add_argument('old_branch',
                        help='Name of the old branch.')
    parser.add_argument('new_branch',
                        help='Name of the new branch.')
    parser.add_argument('projects',
                        help='List of projects to work on.',
                        nargs='*',
                        default=PROJECTS)
    parser.add_argument('-i', '--input',
                        dest='sources',
                        help='Path to a folder containing the git '
                             'repositories.',
                        required=False,
                        default='./sources',
                        type=str,)
    parser.add_argument('-o', '--output',
                        dest='target',
                        help='Directory or file in which data will be saved.\n'
                             'Defaults to "."',
                        required=False,
                        default='.',
                        type=str,)
    parser.add_argument('-f', '--format',
                        dest='format',
                        help='Output format (docbook or rst).',
                        required=False,
                        default='rst',
                        type=str,
                        choices=('docbook', 'rst'),)
    parser.add_argument('-n', '--no-venv-update',
                        dest='novenvupdate',
                        help='Don\'t update the virtual envs.',
                        required=False,
                        action='store_true',
                        default=False,)
    args = parser.parse_args()

    setup_venv(args.projects, args.old_branch, args.novenvupdate)
    setup_venv(args.projects, args.new_branch, args.novenvupdate)

    for project in args.projects:
        old_list = get_options(project, args.old_branch)
        new_list = get_options(project, args.new_branch)

        release = args.new_branch.replace('stable/', '')
        env = get_env(project, release, old_list, new_list)
        ext = 'rst' if args.format == 'rst' else 'xml'
        filename = ("%(project)s-conf-changes.%(ext)s" %
                    {'project': project, 'ext': ext})
        tmpl_file = 'templates/changes.%s.j2' % args.format
        if not os.path.exists(args.target):
            os.makedirs(args.target)
        dest = os.path.join(args.target, filename)

        with open(tmpl_file) as fd:
            template = jinja2.Template(fd.read(), trim_blocks=True)
            output = template.render(**env)

        with open(dest, 'w') as fd:
            fd.write(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
