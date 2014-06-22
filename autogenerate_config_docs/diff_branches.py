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

import git
from lxml import etree


PROJECTS = ['ceilometer', 'cinder', 'glance', 'heat', 'keystone', 'neutron',
            'nova', 'swift', 'trove']


def setup_venv(branch, novenvupdate):
    """Setup a virtual environment for `branch`."""
    dirname = os.path.join('venv', branch.replace('/', '_'))
    if novenvupdate and os.path.exists(dirname):
        return
    if not os.path.exists('venv'):
        os.mkdir('venv')
    args = ["./autohelp-wrapper", "-b", branch, "-e", dirname, "setup"]
    if subprocess.call(args) != 0:
        print("Impossible to create the %s environment." % branch)
        sys.exit(1)


def get_options(project, branch, args):
    """Get the list of known options for a project."""
    print("Working on %(project)s (%(branch)s)" % {'project': project,
                                                   'branch': branch})
    # Checkout the required branch
    repo_path = os.path.join(args.sources, project)
    repo = git.Repo(repo_path)
    repo.heads[branch].checkout()

    # And run autohelp script to get a serialized dict of the discovered
    # options
    dirname = os.path.abspath(os.path.join('venv', branch.replace('/', '_')))
    if project == 'swift':
        cmd = ("python extract_swift_flags.py dump "
               "-s %(sources)s/swift -m %(sources)s/openstack-manuals" %
               {'sources': args.sources})
    else:
        cmd = ("python autohelp.py dump %(project)s -i %(path)s" %
               {'project': project, 'path': repo_path})
    path = os.environ.get("PATH")
    bin_path = os.path.abspath(os.path.join(dirname, "bin"))
    path = "%s:%s" % (bin_path, path)
    serialized = subprocess.check_output(cmd, shell=True,
                                         env={'VIRTUAL_ENV': dirname,
                                              'PATH': path})
    return pickle.loads(serialized)


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


def dbk_append_table(parent, title, cols):
    """Create a docbook table and append it to `parent`.

    :param parent: the element to which the table is added
    :param title: the table title
    :param cols: the number of columns in this table
    """
    table = etree.Element("table")
    parent.append(table)
    caption = etree.Element("caption")
    caption.text = title
    table.append(caption)
    for i in range(cols):
        # We cast to int for python 3
        width = "%d%%" % int(100 / cols)
        table.append(etree.Element("col", width=width))
    return table


def dbk_append_row(parent, cells):
    """Append a row to a table.

    :param parent: the table
    :param cells: a list of strings, one string per column
    """
    tr = etree.Element("tr")
    for text in cells:
        td = etree.Element("td")
        td.text = str(text)
        tr.append(td)
    parent.append(tr)


def dbk_append_header(parent, cells):
    """Append a header to a table.

    :param parent: the table
    :param cells: a list of strings, one string per column
    """
    thead = etree.Element("thead")
    dbk_append_row(thead, cells)
    parent.append(thead)


def diff(old_list, new_list):
    """Compare the old and new lists of options."""
    new_opts = []
    changed_default = []
    deprecated_opts = []
    for name, (group, option) in new_list.items():
        # Find the new options
        if name not in old_list.viewkeys():
            new_opts.append(name)

        # Find the options for which the default value has changed
        elif option.default != old_list[name][1].default:
            changed_default.append(name)

        # Find options that have been deprecated in the new release.
        # If an option name is a key in the old_list dict, it means that it
        # wasn't deprecated.
        for deprecated in option.deprecated_opts:
            # deprecated_opts is a list which always holds at least 1 invalid
            # dict. Forget it.
            if deprecated.name is None:
                continue

            if deprecated.group in [None, 'DEFAULT']:
                full_name = deprecated.name
            else:
                full_name = deprecated.group + '/' + deprecated.name

            if full_name in old_list.viewkeys():
                deprecated_opts.append((full_name, name))

    return new_opts, changed_default, deprecated_opts


def format_option_name(name):
    """Return a formatted string for the option path."""
    try:
        section, name = name.split('/')
    except ValueError:
        # name without a section ('log_dir')
        return "[DEFAULT]/%s" % name

    try:
        # If we're dealing with swift, we'll have a filename to extract
        # ('proxy-server|filter:tempurl/use')
        filename, section = section.split('|')
        return "%s.conf: [%s]/%s" % (filename, section, name)
    except ValueError:
        # section but no filename ('database/connection')
        return "[%s]/%s" % (section, name)


def generate_docbook(project, new_branch, old_list, new_list):
    """Generate the diff between the 2 options lists for `project`."""
    new_opts, changed_default, deprecated_opts = diff(old_list, new_list)

    XMLNS = '{http://www.w3.org/XML/1998/namespace}'
    DOCBOOKMAP = {None: "http://docbook.org/ns/docbook"}

    section = etree.Element("section", nsmap=DOCBOOKMAP, version="5.0")
    id = "%(project)s-conf-changes-%(branch)s" % {'project': project,
                                                  'branch': new_branch}
    section.set(XMLNS + 'id', id)
    section.append(etree.Comment(" Warning: Do not edit this file. It is "
                                 "automatically generated and your changes "
                                 "will be overwritten. The tool to do so "
                                 "lives in the openstack-doc-tools "
                                 "repository. "))
    title = etree.Element("title")
    title.text = "New, updated and deprecated options for %s" % project
    section.append(title)

    # New options
    if new_opts:
        table = dbk_append_table(section, "New options", 2)
        dbk_append_header(table, ["Option = default value",
                                  "(Type) Help string"])
        for name in sorted(new_opts, _cmpopts):
            opt = new_list[name][1]
            type = opt.__class__.__name__.split('.')[-1]
            name = format_option_name(name)
            cells = ["%(name)s = %(default)s" % {'name': name,
                                                 'default': opt.default},
                     "(%(type)s) %(help)s" % {'type': type, 'help': opt.help}]
            dbk_append_row(table, cells)

    # Updated default
    if changed_default:
        table = dbk_append_table(section, "New default values", 3)
        dbk_append_header(table, ["Option", "Previous default value",
                                  "New default value"])
        for name in sorted(changed_default, _cmpopts):
            old_default = old_list[name][1].default
            new_default = new_list[name][1].default
            if isinstance(old_default, list):
                old_default = ", ".join(old_default)
            if isinstance(new_default, list):
                new_default = ", ".join(new_default)
            name = format_option_name(name)
            cells = [name, old_default, new_default]
            dbk_append_row(table, cells)

    # Deprecated options
    if deprecated_opts:
        table = dbk_append_table(section, "Deprecated options", 2)
        dbk_append_header(table, ["Deprecated option", "New Option"])
        for deprecated, new in deprecated_opts:
            deprecated = format_option_name(deprecated)
            new = format_option_name(new)
            dbk_append_row(table, [deprecated, new])

    return etree.tostring(section, pretty_print=True, xml_declaration=True,
                          encoding="UTF-8")


def main():
    parser = argparse.ArgumentParser(
        description='Generate a summary of configuration option changes.',
        usage='%(prog)s <old_branch> <new_branch> [options]')
    parser.add_argument('old_branch',
                        help='Name of the old branch.')
    parser.add_argument('new_branch',
                        help='Name of the new branch.')
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
    parser.add_argument('-n', '--no-venv-update',
                        dest='novenvupdate',
                        help='Don\'t update the virtual envs.',
                        required=False,
                        action='store_true',
                        default=False,)
    args = parser.parse_args()

    # Blacklist trove if we diff between havana and icehouse: autohelp.py fails
    # with trove on havana
    if args.old_branch == "stable/havana":
        PROJECTS.remove('trove')

    setup_venv(args.old_branch, args.novenvupdate)
    setup_venv(args.new_branch, args.novenvupdate)

    for project in PROJECTS:
        old_list = get_options(project, args.old_branch, args)
        new_list = get_options(project, args.new_branch, args)

        release = args.new_branch.replace('stable/', '')
        xml = generate_docbook(project, release, old_list, new_list)
        filename = ("%(project)s-conf-changes-%(release)s.xml" %
                    {'project': project, 'release': release})
        if not os.path.exists(args.target):
            os.makedirs(args.target)
        dest = os.path.join(args.target, filename)
        with open(dest, 'w') as fd:
            fd.write(xml)

    return 0


if __name__ == "__main__":
    sys.exit(main())
