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

from docutils import core
from docutils import io
from docutils import nodes
import jinja2
from lxml import etree
from oslo_config import cfg

from autohelp import OptionsCache  # noqa

# Swift configuration example files live in
# swift/etc/*.conf-sample
# and contain sections enclosed in [], with
# options one per line containing =
# and generally only having a single entry
# after the equals (the default value)

DBK_NS = ".//{http://docbook.org/ns/docbook}"

BASE_XML = '''<?xml version="1.0"?>
<para xmlns="http://docbook.org/ns/docbook"
  version="5.0">
<!-- The tool that generated this table lives in the
     openstack-doc-tools repository. The editions made in
     this file will *not* be lost if you run the script again. -->
  <table rules="all">
    <caption>Description of configuration options for
        <literal>[%s]</literal> in <filename>%s.conf</filename>
    </caption>
    <col width="50%%"/>
    <col width="50%%"/>
    <thead>
      <tr>
        <th>Configuration option = Default value</th>
        <th>Description</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>
</para>'''


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


def get_existing_options_from_rst(optfiles):
    """Parse an existing RST table to compile a list of existing options."""
    options = {}
    for optfile in optfiles:
        input_string = open(optfile).read().replace(':ref:', '')
        output, pub = core.publish_programmatically(
            source_class=io.StringInput, source=input_string,
            source_path=optfile, destination_class=io.NullOutput,
            destination=None, destination_path='/dev/null', reader=None,
            reader_name='standalone', parser=None,
            parser_name='restructuredtext', writer=None, writer_name='null',
            settings=None, settings_spec=None, settings_overrides=None,
            config_section=None, enable_exit_status=None)
        doc = pub.writer.document
        data = dict(doc.traverse(nodes.row, include_self=False)[1:])
        for a, b in data.items():
            option = str(a.traverse(nodes.literal)[0].children[0])
            helptext = str(b.traverse(nodes.paragraph)[0].children[0])

            if option not in options or 'No help text' in options[option]:
                # options[option.split('=',1)[0]] = helptext
                options[option] = helptext.strip()

    return options


def get_existing_options(optfiles):
    """Parse an existing XML table to compile a list of existing options."""
    options = {}
    for optfile in optfiles:
        if optfile.endswith('/swift-conf-changes.xml'):
            continue
        xml = etree.fromstring(open(optfile).read().replace(':ref:', ''))
        tbody = xml.find(DBK_NS + "tbody")
        trlist = tbody.findall(DBK_NS + "tr")
        for tr in trlist:
            try:
                col1, col2 = tr.findall(DBK_NS + "td")
                option = col1.find(DBK_NS + "option").text
                helptext = etree.tostring(col2, xml_declaration=False,
                                          method="text")
            except IndexError:
                continue
            if option not in options or 'No help text' in options[option]:
                # options[option.split('=',1)[0]] = helptext
                options[option] = helptext.strip()
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


def write_files(options, manuals_repo, output_format):
    """Create new DocBook tables.

    Writes a set of DocBook-formatted tables, one per section in swift
    configuration files.
    """
    all_options = {}
    names = options.get_option_names()
    for full_option in sorted(names, OptionsCache._cmpopts):
        section, optname = full_option.split('/')
        oslo_opt = options.get_option(full_option)[1]
        all_options.setdefault(section, [])

        helptext = oslo_opt.help.strip().replace('\n', ' ')
        helptext = ' '.join(helptext.split())
        all_options[section].append((oslo_opt.name,
                                     oslo_opt.default,
                                     helptext))

    for full_section, options in all_options.items():
        sample_filename, section = full_section.split('|')
        tmpl_file = os.path.join(os.path.dirname(__file__),
                                 'templates/swift.%s.j2' % output_format)
        with open(tmpl_file) as fd:
            template = jinja2.Template(fd.read(), trim_blocks=True)
            output = template.render(filename=sample_filename,
                                     section=section,
                                     options=options)

        if output_format == 'docbook':
            tgt = (manuals_repo + '/doc/common/tables/' + 'swift-' +
                   sample_filename + '-' + section + '.xml')
        else:
            tgt = (manuals_repo + '/doc/config-reference/source/tables/' +
                   'swift-' + sample_filename + '-' + section + '.rst')

        with open(tgt, 'w') as fd:
            fd.write(output)


def read_options(swift_repo, manuals_repo, read_from, verbose):
    """Find swift configuration options.

    Uses existing tables and swift devref as a source of truth in that order to
    determine helptext for options found in sample config files.
    """

    if read_from == 'rst':
        options = get_existing_options_from_rst(
            glob.glob(manuals_repo +
                      '/doc/config-reference/source/tables/swift*rst'))
    else:
        options = get_existing_options(
            glob.glob(manuals_repo + '/doc/common/tables/swift*xml'))

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
                        print(parsed_line[0] + " has no help text")

                # \xa0 is a non-breacking space
                name = parsed_line[0]
                option_desc = option_desc.replace(u'\xa0', u' ')
                default = parsed_line[1]

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
        usage=("%(prog)s docbook|rst|dump [-v] [-s swift_repo] "
               "[-m manuals_repo]"))
    parser.add_argument('subcommand',
                        help='Action (docbook, rst, dump).',
                        choices=['docbook', 'dump', 'rst'])
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
    parser.add_argument('-f', '--from',
                        dest='read_from',
                        help="Source to get defined options (rst or docbook)",
                        required=False,
                        default='rst',
                        choices=['rst', 'docbook'])
    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        dest='verbose',
                        required=False)
    args = parser.parse_args()

    # Avoid cluttering the pickle output, otherwise it's not usable
    if args.subcommand == 'dump':
        args.verbose = 0

    read_options(args.swift_repo,
                 args.manuals_repo,
                 args.read_from,
                 args.verbose)
    options = OptionsCache()

    if args.subcommand in ('docbook', 'rst'):
        write_files(options, args.manuals_repo, args.subcommand)

    elif args.subcommand == 'dump':
        options.dump()

    return 0

if __name__ == "__main__":
    sys.exit(main())
