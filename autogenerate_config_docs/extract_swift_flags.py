#!/usr/bin/env python
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

import argparse
import glob
import os
import pickle
import sys
from xml.dom import minidom
import xml.sax.saxutils

from autohelp import OptionsCache
from oslo.config import cfg

# Swift configuration example files live in
# swift/etc/*.conf-sample
# and contain sections enclosed in [], with
# options one per line containing =
# and generally only having a single entry
# after the equals (the default value)


def parse_line(line):
    """Parse a line.

    Takes a line from a swift sample configuration file and attempts
    to separate the lines with actual configuration option and default
    value from the rest. Returns None if the line doesn't appear to
    contain a valid configuration option = default value pair, and
    a pair of the config and its default if it does.
    """

    if '=' not in line:
        return None
    temp_line = line.strip('#').strip()
    config, default = temp_line.split('=', 1)
    config = config.strip()
    if ' ' in config and config[0:3] != 'set':
        if len(default.split()) > 1 or config[0].isupper():
            return None
    if len(config) < 2 or '.' in config or '<' in config or '>' in config:
        return None
    return config, default.strip()


def get_existing_options(optfiles):
    """Parse an existing XML table to compile a list of existing options."""
    options = {}
    for optfile in optfiles:
        if '/swift-conf-changes-' in optfile:
            continue
        xmldoc = minidom.parse(optfile)
        tbody = xmldoc.getElementsByTagName('tbody')[0]
        trlist = tbody.getElementsByTagName('tr')
        for tr in trlist:
            try:
                tdlist = tr.getElementsByTagName('td')
                optentry = tdlist[0].childNodes[0].nodeValue
                option = optentry.split('=', 1)[0].strip()
                helptext = tdlist[1].childNodes[0].nodeValue
            except IndexError:
                continue
            if option not in options or 'No help text' in options[option]:
                # options[option.split('=',1)[0]] = helptext
                options[option] = helptext
    return options


def extract_descriptions_from_devref(swift_repo, options):
    """Extract descriptions from devref RST files.

    Loop through the devref RST files, looking for lines formatted
    such that they might contain a description of a particular
    option.
    """

    option_descs = {}
    rsts = glob.glob(swift_repo + '/doc/source/*.rst')
    for rst in rsts:
        rst_file = open(rst, 'r')
        in_option_block = False
        prev_option = None
        for line in rst_file:
            if 'Option    ' in line:
                in_option_block = True
            if in_option_block:
                if '========' in line:
                    in_option_block = False
                    continue
                if line[0] == ' ' and prev_option is not None:
                    option_descs[prev_option] = (option_descs[prev_option]
                                                 + ' ' + line.strip())
                for option in options:
                    line_parts = line.strip().split(None, 2)
                    if ('   ' in line and
                            len(line_parts) == 3 and
                            option == line_parts[0] and
                            line_parts[1] != '=' and
                            option != 'use' and
                            (option not in option_descs or
                             len(option_descs[option]) < len(line_parts[2]))):
                        option_descs[option] = line_parts[2]
                        prev_option = option
    return option_descs


def new_section_file(manuals_repo, section):
    """Create a new section file.

    It writes the DocBook header and the first table row.
    Returns a file descriptor for this new file.
    """

    # The section holds 2 informations, the file in which the option was found,
    # and the section name in that file.
    sample, section_name = section.split('|')
    section_filename = (manuals_repo + '/doc/common/tables/' +
                        'swift-' + sample + '-' + section_name + '.xml')
    section_fd = open(section_filename, 'w')
    section_fd.write('''<?xml version="1.0" encoding="UTF-8"?>
    <!-- The tool that generated this table lives in the
         openstack-doc-tools repository. The editions made in
         this file will *not* be lost if you run the script again. -->
    <para xmlns="http://docbook.org/ns/docbook" version="5.0">
    <table rules="all">
    <caption>Description of configuration options for <literal>'''
                     + '[' + section_name + ']' + '</literal> in <literal>'
                     + sample + '.conf' +
                     '''</literal></caption>
    <col width="50%"/>
    <col width="50%"/>
    <thead>
        <tr>
            <th>Configuration option = Default value</th>
            <th>Description</th>
        </tr>
    </thead>
    <tbody>''')
    return section_fd


def write_docbook(options, manuals_repo):
    """Create new DocBook tables.

    Writes a set of DocBook-formatted tables, one per section in swift
    configuration files.
    """
    def end_file(fd):
        fd.write('''
    </tbody>
    </table>
    </para>''')

    names = options.get_option_names()
    current_section = None
    section_fd = None
    for full_option in sorted(names, OptionsCache._cmpopts):
        section, optname = full_option.split('/')

        if current_section != section:
            if section_fd is not None:
                end_file(section_fd)
                section_fd.close()
            current_section = section
            section_fd = new_section_file(manuals_repo, section)

        oslo_opt = options.get_option(full_option)[1]
        section_fd.write('\n        <tr>\n'
                         '            <td>' +
                         oslo_opt.name + ' = ' +
                         oslo_opt.default +
                         '</td><td>' + oslo_opt.help + '</td>\n' +
                         '        </tr>')
    end_file(section_fd)


def read_options(swift_repo, manuals_repo, verbose):
    """Find swift configuration options.

    Uses existing tables and swift devref as a source of truth in that order to
    determine helptext for options found in sample config files.
    """

    existing_tables = glob.glob(manuals_repo + '/doc/common/tables/swift*xml')
    options = {}
    # use the existing tables to get a list of option names
    options = get_existing_options(existing_tables)
    option_descs = extract_descriptions_from_devref(swift_repo, options)
    conf_samples = glob.glob(swift_repo + '/etc/*conf-sample')
    for sample in conf_samples:
        current_section = None
        sample_file = open(sample, 'r')
        for line in sample_file:
            if '[' in line and ']\n' in line and '=' not in line:
                # It's a header line in the conf file, open a new table file
                # for this section and close any existing one
                new_line = line.strip('#').strip()
                if current_section != new_line:
                    current_section = new_line

                    base_section = os.path.basename(sample).split('.conf')[0]
                    extra_section = current_section[1:-1].replace(':', '-')
                    full_section = "%s|%s" % (base_section, extra_section)

                    continue

            # All the swift files start with a section, except the rsync
            # sample. The first items are not important for us.
            if current_section is None:
                continue

            # It's a config option line in the conf file, find out the
            # help text and write to the table file.
            parsed_line = parse_line(line)
            if parsed_line is not None:
                if (parsed_line[0] in options.keys()
                   and 'No help text' not in options[parsed_line[0]]):
                    # use the help text from existing tables
                    option_desc = options[parsed_line[0]]
                elif parsed_line[0] in option_descs:
                    # use the help text from the devref
                    option_desc = option_descs[parsed_line[0]]
                else:
                    option_desc = 'No help text available for this option.'
                    if verbose > 0:
                        print(parsed_line[0] + "has no help text")

                # \xa0 is a non-breacking space
                name = parsed_line[0]
                option_desc = option_desc.replace(u'\xa0', u' ')
                default = xml.sax.saxutils.escape(str(parsed_line[1]))

                o = cfg.StrOpt(name=name, default=default, help=option_desc)
                try:
                    cfg.CONF.register_opt(o, full_section)
                except cfg.DuplicateOptError:
                    pass


def dump_options(options):
    """Dump the list of options with their attributes.

    This output is consumed by the diff_branches script.
    """
    print(pickle.dumps(options._opts_by_name))


def main():
    """Parse and write the Swift configuration options."""

    parser = argparse.ArgumentParser(
        description="Update the swift options tables.",
        usage="%(prog)s docbook|dump [-v] [-s swift_repo] [-m manuals_repo]")
    parser.add_argument('subcommand',
                        help='Action (docbook, dump).',
                        choices=['docbook', 'dump'])
    parser.add_argument('-s', '--swift-repo',
                        dest='swift_repo',
                        help="Location of the swift git repository.",
                        required=False,
                        default="./sources/swift")
    parser.add_argument('-m', '--manuals-repo',
                        dest='manuals_repo',
                        help="Location of the manuals git repository.",
                        required=False,
                        default="./sources/openstack-manuals")
    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        dest='verbose',
                        required=False)
    args = parser.parse_args()

    # Avoid cluttering the pickle output, otherwise it's not usable
    if args.subcommand == 'dump':
        args.verbose = 0

    read_options(args.swift_repo, args.manuals_repo, args.verbose)
    options = OptionsCache()

    if args.subcommand == 'docbook':
        write_docbook(options, args.manuals_repo)

    elif args.subcommand == 'dump':
        dump_options(options)

    return 0

if __name__ == "__main__":
    sys.exit(main())
