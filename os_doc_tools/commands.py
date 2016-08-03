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

import argparse
import os
import re
import subprocess
import sys
import yaml

import os_doc_tools

DEVNULL = open(os.devnull, 'wb')
MAXLINELENGTH = 78


def use_help_flag(os_command):
    """Use --help flag (instead of help keyword)

    Returns true if the command requires a --help flag instead
    of a help keyword.
    """

    return os_command == "swift" or "-manage" in os_command


def quote_rst(line):
    """Convert special characters for RST output."""

    line = line.replace('\\', '\\\\').replace('`', '\\`').replace('*', '\\*')

    if '--' in line:
        line = re.sub(r'(--[^ .\'\\]*)', r":option:`\1`", line)
        # work around for "`--`" at murano
        line = line.replace('\\`:option:`--`\\`', '```--```')

    if 'DEPRECATED!' in line:
        line = line.replace('DEPRECATED!', '**DEPRECATED!**')
    elif 'DEPRECATED' in line:
        line = line.replace('DEPRECATED', '**DEPRECATED**')

    if 'env[' in line:
        line = line.replace('env[', '``env[').replace(']', ']``')
        # work around for "Default=env[...]" at cinder
        line = line.replace('=``', '= ``')

    return line


def generate_heading(os_command, api_name, title,
                     output_dir, os_filename, continue_on_error):
    """Write RST file header.

    :param os_command:        client command to document
    :param api_name:          string description of the API of os_command
    :param output_dir:        directory to write output file to
    :param os_filename:       name to create current output file as
    :param continue_on_error: continue even if there's an error
    """

    try:
        version = subprocess.check_output([os_command, "--version"],
                                          universal_newlines=True,
                                          stderr=subprocess.STDOUT)
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            action = 'skipping' if continue_on_error else 'aborting'
            print("Command %s not found, %s." % (os_command, action))
            if continue_on_error:
                return
            else:
                sys.exit(1)
    # Extract version from "swift 0.3"
    version = version.splitlines()[-1].strip().rpartition(' ')[2]

    print("Documenting '%s help (version %s)'" % (os_command, version))

    os_file = open(os.path.join(output_dir, os_filename), 'w')
    os_file.write(".. ##  WARNING  #####################################\n")
    os_file.write(".. This file is tool-generated. Do not edit manually.\n")
    os_file.write(".. ##################################################\n\n")
    format_heading(title, 1, os_file)

    if os_command == "heat":
        os_file.write(".. warning::\n\n")
        os_file.write("   The " + os_command + " CLI is deprecated\n")
        os_file.write("   in favor of python-openstackclient.\n")
        os_file.write("   For more information, see :doc:`openstack`.\n")
        os_file.write("   For a Python library, continue using\n")
        os_file.write("   python-" + os_command + "client.\n\n")

    if os_command == "openstack":
        os_file.write("The openstack client is a common OpenStack")
        os_file.write("command-line interface (CLI).\n\n")
    else:
        os_file.write("The " + os_command + " client is the command-line ")
        os_file.write("interface (CLI) for\n")
        os_file.write("the " + api_name + " and its extensions.\n\n")

    os_file.write("This chapter documents :command:`" + os_command + "` ")
    os_file.write("version ``" + version + "``.\n\n")

    os_file.write("For help on a specific :command:`" + os_command + "` ")
    os_file.write("command, enter:\n\n")

    os_file.write(".. code-block:: console\n\n")
    if use_help_flag(os_command):
        os_file.write("   $ " + os_command + " COMMAND --help\n\n")
    else:
        os_file.write("   $ " + os_command + " help COMMAND\n\n")

    os_file.write(".. _" + os_command + "_command_usage:\n\n")
    format_heading(os_command + " usage", 2, os_file)
    return os_file


def is_option(string):
    """Returns True if string specifies an argument."""

    for x in string:
        if not (x.isupper() or x == '_' or x == ','):
            return False

    if string.startswith('DEPRECATED'):
        return False
    return True


def extract_options(line):
    """Extract command or option from line."""

    # We have a command or parameter to handle
    # Differentiate:
    #  1. --version
    #  2. --timeout <seconds>
    #  3. --service <service>, --service-id <service>
    #  4. -v, --verbose
    #  5. -p PORT, --port PORT
    #  6. <backup>              ID of the backup to restore.
    #  7. --alarm-action <Webhook URL>
    #  8.   <NAME or ID>  Name or ID of stack to resume.
    #  9. --json JSON  JSON representation of node group template.
    # 10. --id <cluster_id> ID of the cluster to show.
    # 11. --instance "<opt=value,opt=value,...>"

    split_line = line.split(None, 2)

    if split_line[0].startswith("-"):
        last_was_option = True
    else:
        last_was_option = False

    if (len(split_line) > 1 and
        ('<' in split_line[0] or
         '<' in split_line[1] or
         '--' in split_line[1] or
         split_line[1].startswith(("-", '<', '{', '[')) or
         is_option(split_line[1]))):

        words = line.split(None)

        i = 0
        while i < len(words) - 1:
            if (('<' in words[i] and
                '>' not in words[i]) or
                ('[' in words[i] and
                 ']' not in words[i])):
                words[i] += ' ' + words[i + 1]
                del words[i + 1]
            else:
                i += 1

        skip_is_option = False
        while len(words) > 1:
            if words[1].startswith('DEPRECATED'):
                break
            if last_was_option:
                if (words[1].startswith(("-", '<', '{', '[', '"')) or
                   (is_option(words[1]) and skip_is_option is False)):
                    skip_is_option = False
                    if words[1].isupper() or words[1].startswith('<'):
                        skip_is_option = True
                    words[0] = words[0] + ' ' + words[1]
                    del words[1]
                else:
                    break
            else:
                if words[1].startswith("-"):
                    words[0] = words[0] + ' ' + words[1]
                    del words[1]
                else:
                    break

        w0 = words[0]
        del words[0]
        w1 = ''
        if words:
            w1 = words[0]
            del words[0]
            for w in words:
                w1 += " " + w

        if not w1:
            split_line = [w0]
        else:
            split_line = [w0, w1]
    else:
        split_line = line.split(None, 1)

    return split_line


def format_heading(heading, level, os_file):
    """Nicely print heading.

    :param heading: heading strings
    :param level: heading level
    :param os_file: open filehandle for output of RST file
    """

    if level == 1:
        os_file.write("=" * len(heading) + "\n")

    os_file.write(heading + "\n")

    if level == 1:
        os_file.write("=" * len(heading) + "\n\n")
    elif level == 2:
        os_file.write("~" * len(heading) + "\n\n")
    elif level == 3:
        os_file.write("-" * len(heading) + "\n\n")
    else:
        os_file.write("\n")

    return


def format_help(title, lines, os_file):
    """Nicely print section of lines.

    :param title: help title, if exist
    :param lines: strings to format
    :param os_file: open filehandle for output of RST file
    """

    close_entry = False
    if title:
        os_file.write("**" + title + ":**" + "\n\n")

    continued_line = ''
    for line in lines:
        if not line or line[0] != ' ':
            break
        # We have to handle these cases:
        # 1. command  Explanation
        # 2. command
        #             Explanation on next line
        # 3. command  Explanation continued
        #             on next line
        # If there are more than 8 spaces, let's treat it as
        # explanation.
        if line.startswith('       '):
            # Explanation
            xline = continued_line + quote_rst(line.lstrip(' '))
            continued_line = ''
            # Concatenate the command options with "-"
            # For example:
            #     see 'glance image-
            #     show'
            if xline.endswith('-'):
                continued_line = xline
                continue
            # check niceness
            if len(xline) > (MAXLINELENGTH - 2):
                xline = xline.replace(' ', '\n  ')
            os_file.write("  " + xline + "\n")
            continue
        # Now we have a command or parameter to handle
        split_line = extract_options(line)

        if not close_entry:
            close_entry = True
        else:
            os_file.write("\n")

        xline = split_line[0]

        # check niceness work around for long option name, glance
        xline = xline.replace('[<RESOURCE_TYPE_ASSOCIATIONS> ...]',
                              '[...]')

        os_file.write("``" + xline + "``\n")

        if len(split_line) > 1:
            # Explanation
            xline = continued_line + quote_rst(split_line[1])
            continued_line = ''
            # Concatenate the command options with "-"
            # For example:
            #     see 'glance image-
            #     show'
            if xline.endswith('-'):
                continued_line = xline
                continue
            # check niceness
            if len(xline) > (MAXLINELENGTH - 2):
                # check niceness
                xline = xline.replace(' ', '\n  ')
            os_file.write("  " + xline + "\n")

    os_file.write("\n")

    return


def generate_command(os_command, os_file):
    """Convert os_command --help to RST.

    :param os_command: client command to document
    :param os_file:    open filehandle for output of RST file
    """

    if use_help_flag(os_command):
        help_lines = subprocess.check_output([os_command, "--help"],
                                             universal_newlines=True,
                                             stderr=DEVNULL).split('\n')
    else:
        help_lines = subprocess.check_output([os_command, "help"],
                                             universal_newlines=True,
                                             stderr=DEVNULL).split('\n')

    ignore_next_lines = False
    next_line_screen = True
    line_index = -1
    in_screen = False
    subcommands = 'complete'
    for line in help_lines:
        line_index += 1
        if line and line[0] != ' ':
            # XXX: Might have whitespace before!!
            if '<subcommands>' in line:
                ignore_next_lines = False
                continue
            if 'Positional arguments' in line:
                ignore_next_lines = True
                next_line_screen = True
                os_file.write("\n\n")
                in_screen = False
                if os_command != "glance":
                    format_help('Subcommands',
                                help_lines[line_index + 2:], os_file)
                continue
            if line.startswith(('Optional arguments:', 'Optional:',
                                'Options:', 'optional arguments')):
                if in_screen:
                    os_file.write("\n\n")
                    in_screen = False
                os_file.write(".. _" + os_command + "_command_options:\n\n")
                format_heading(os_command + " optional arguments", 2, os_file)
                format_help('', help_lines[line_index + 1:], os_file)
                next_line_screen = True
                ignore_next_lines = True
                continue
            # magnum and sahara
            if line.startswith('Common auth options'):
                if in_screen:
                    os_file.write("\n\n")
                    in_screen = False
                os_file.write("\n")
                os_file.write(os_command)
                os_file.write(".. _" + os_command + "_common_auth:\n\n")
                format_heading(os_command + " common authentication arguments",
                               2, os_file)
                format_help('', help_lines[line_index + 1:], os_file)
                next_line_screen = True
                ignore_next_lines = True
                continue
            # neutron
            if line.startswith('Commands for API v2.0:'):
                if in_screen:
                    os_file.write("\n\n")
                    in_screen = False
                os_file.write(".. _" + os_command + "_common_api_v2:\n\n")
                format_heading(os_command + " API v2.0 commands", 2, os_file)
                format_help('', help_lines[line_index + 1:], os_file)
                next_line_screen = True
                ignore_next_lines = True
                continue
            # swift
            if line.startswith('Examples:'):
                os_file.write(".. _" + os_command + "_examples:\n\n")
                format_heading(os_command + " examples", 2, os_file)
                next_line_screen = True
                ignore_next_lines = False
                continue
            # all
            if not line.startswith('usage'):
                continue
        if not ignore_next_lines:
            if next_line_screen:
                os_file.write(".. code-block:: console\n\n")
                os_file.write("   " + line)
                next_line_screen = False
                in_screen = True
            elif line:
                os_file.write("\n   " + line.rstrip())
        # subcommands (select bash-completion, complete for bash-completion)
        if 'bash-completion' in line:
            subcommands = 'bash-completion'

    if in_screen:
        os_file.write("\n\n")

    return subcommands


def generate_subcommand(os_command, os_subcommand, os_file, extra_params,
                        suffix, title_suffix):
    """Convert os_command help os_subcommand to RST.

    :param os_command: client command to document
    :param os_subcommand: client subcommand to document
    :param os_file:    open filehandle for output of RST file
    :param extra_params: Extra parameter to pass to os_command
    :param suffix: Extra suffix to add to link ID
    :param title_suffix: Extra suffix for title
    """

    print("Documenting subcommand '%s'..." % os_subcommand)

    args = [os_command]
    if extra_params:
        args.extend(extra_params)
    if use_help_flag(os_command):
        args.append(os_subcommand)
        args.append("--help")
    else:
        args.append("help")
        args.append(os_subcommand)
    help_lines = subprocess.check_output(args,
                                         universal_newlines=True,
                                         stderr=DEVNULL)

    help_lines_lower = help_lines.lower()
    if 'positional arguments' in help_lines_lower:
        index = help_lines_lower.index('positional arguments')
    elif 'optional arguments' in help_lines_lower:
        index = help_lines_lower.index('optional arguments')
    else:
        index = len(help_lines_lower)

    if 'deprecated' in (help_lines_lower[0:index]):
        print("Subcommand '%s' is deprecated, skipping." % os_subcommand)
        return

    help_lines = help_lines.split('\n')

    os_subcommandid = os_subcommand.replace(' ', '_')
    os_file.write(".. _" + os_command + "_" + os_subcommandid + suffix)
    os_file.write(":\n\n")
    format_heading(os_command + " " + os_subcommand + title_suffix, 3, os_file)

    if os_command == "swift":
        next_line_screen = False
        os_file.write(".. code-block:: console\n\n")
        os_file.write("Usage: swift " + os_subcommand + "\n\n")
        in_para = True
    else:
        next_line_screen = True
        in_para = False
    if extra_params:
        extra_paramstr = ' '.join(extra_params)
        help_lines[0] = help_lines[0].replace(os_command, "%s %s" %
                                              (os_command, extra_paramstr))
    line_index = -1
    # Content is:
    # usage...
    #
    # Description
    #
    # Arguments

    skip_lines = False
    for line in help_lines:
        line_index += 1
        if line.startswith('Usage:') and os_command == "swift":
            line = line[len("Usage: "):]
        if line.startswith(('Arguments:', 'Positional arguments:',
                            'positional arguments', 'Optional arguments',
                            'optional arguments')):
            if in_para:
                in_para = False
                os_file.write("\n")
            if line.startswith(('Positional arguments',
                                'positional arguments')):
                format_help('Positional arguments',
                            help_lines[line_index + 1:], os_file)
                skip_lines = True
                continue
            elif line.startswith(('Optional arguments:',
                                  'optional arguments')):
                format_help('Optional arguments',
                            help_lines[line_index + 1:], os_file)
                break
            else:
                format_help('Arguments', help_lines[line_index + 1:], os_file)
                break
        if skip_lines:
            continue
        if not line:
            if not in_para:
                os_file.write("\n")
            in_para = True
            continue
        if next_line_screen:
            os_file.write(".. code-block:: console\n\n")
            os_file.write("   " + line + "\n")
            next_line_screen = False
        elif line.startswith('       '):
            # ceilometer alarm-gnocchi-aggregation-by-metrics-threshold-create
            # has 7 white space indentation
            if not line.isspace():
                # skip blank line, such as "trove help cluster-grow" command.
                os_file.write("   " + line + "\n")
        else:
            xline = quote_rst(line)
            if (len(xline) > MAXLINELENGTH):
                # check niceness
                xline = xline.replace(' ', '\n')
            os_file.write(xline + "\n")

    if in_para:
        os_file.write("\n")


def discover_subcommands(os_command, subcommands, extra_params):
    """Discover all help subcommands for the given command"

    :param os_command: client command whose subcommands need to be discovered
    :param subcommands: list or type ('complete' or 'bash-completion')
                        of subcommands to document
    :param extra_params: Extra parameter to pass to os_command.
    :return: the list of subcommands discovered
    :rtype: list(str)
    """
    if extra_params is None:
        extra_params = ''
    print(("Discovering subcommands of '%s' %s ..."
          % (os_command, extra_params)))
    blacklist = ['bash-completion', 'complete', 'help']
    if type(subcommands) is str:
        args = [os_command]
        if extra_params:
            args.extend(extra_params)
        if subcommands == 'complete':
            subcommands = []
            args.append('complete')
            lines = subprocess.check_output(
                args, universal_newlines=True, stderr=DEVNULL).split('\n')
            delim = ' '
            # if the cmds= line contains '-' then use that as a delim
            for line in lines:
                if '-' in line and 'cmds=' in line:
                    delim = '-'
                    break
            for line in [x.strip() for x in lines
                         if x.strip().startswith('cmds_') and '-' in x]:
                subcommand, _ = line.split('=')
                subcommand = subcommand.replace(
                    'cmds_', '').replace('_', delim)
                subcommands.append(subcommand)
        else:
            args.append('bash-completion')
            subcommands = subprocess.check_output(
                args,
                universal_newlines=True).strip().split('\n')[-1].split()

    subcommands = sorted([o for o in subcommands if not (o.startswith('-') or
                                                         o in blacklist)])

    print("%d subcommands discovered." % len(subcommands))
    return subcommands


def generate_subcommands(os_command, os_file, subcommands, extra_params,
                         suffix, title_suffix):
    """Convert os_command help subcommands for all subcommands to RST.

    :param os_command: client command to document
    :param os_file:    open filehandle for output of RST file
    :param subcommands: list or type ('complete' or 'bash-completion')
                        of subcommands to document
    :param extra_params: Extra parameter to pass to os_command.
    :param suffix: Extra suffix to add to link ID
    :param title_suffix: Extra suffix for title
    """
    for subcommand in subcommands:
        generate_subcommand(os_command, subcommand, os_file, extra_params,
                            suffix, title_suffix)
    print("%d subcommands documented." % len(subcommands))


def discover_and_generate_subcommands(os_command, os_file, subcommands,
                                      extra_params, suffix, title_suffix):
    """Convert os_command help subcommands for all subcommands to RST.

    :param os_command: client command to document
    :param os_file:    open filehandle for output of RST file
    :param subcommands: list or type ('complete' or 'bash-completion')
                        of subcommands to document
    :param extra_params: Extra parameter to pass to os_command.
    :param suffix: Extra suffix to add to link ID
    :param title_suffix: Extra suffix for title
    """
    subcommands = discover_subcommands(os_command, subcommands, extra_params)
    generate_subcommands(os_command, os_file, subcommands, extra_params,
                         suffix, title_suffix)


def _get_clients_filename():
    return os.path.join(os.path.dirname(__file__),
                        'resources/clients.yaml')


def get_clients():
    """Load client definitions from the resource file."""
    fname = _get_clients_filename()
    clients = yaml.load(open(fname, 'r'))
    return clients


def document_single_project(os_command, output_dir, continue_on_error):
    """Create documentation for os_command."""

    clients = get_clients()

    if os_command not in clients:
        print("'%s' command not yet handled" % os_command)
        print("(Command must be defined in '%s')" % _get_clients_filename())
        if continue_on_error:
            return False
        else:
            sys.exit(-1)

    print("Documenting '%s'" % os_command)

    data = clients[os_command]
    if 'name' in data:
        api_name = "%s API" % data['name']
        title = "%s command-line client" % data.get('title', data['name'])
    else:
        api_name = ''
        title = data.get('title', '')

    out_filename = os_command + ".rst"
    out_file = generate_heading(os_command, api_name, title,
                                output_dir, out_filename,
                                continue_on_error)
    if not out_file:
        if continue_on_error:
            return False
        else:
            sys.exit(-1)

    subcommands = generate_command(os_command, out_file)
    if subcommands == 'complete' and data.get('subcommands'):
        subcommands = data.get('subcommands')

    if os_command == 'cinder':
        format_heading("Block Storage API v2 commands", 2, out_file)

        out_file.write("You can select an API version to use by adding the\n")
        out_file.write(":option:`--os-volume-api-version` parameter or by\n")
        out_file.write("setting the corresponding environment variable:\n\n")

        out_file.write(".. code-block:: console\n\n")
        out_file.write("   export OS_VOLUME_API_VERSION=2\n\n")

        discover_and_generate_subcommands(os_command, out_file, subcommands,
                                          ["--os-volume-api-version", "2"],
                                          "", "")
    elif os_command == 'openstack':
        format_heading("OpenStack with Identity API v3 commands", 2, out_file)

        out_file.write(".. important::\n\n")
        out_file.write("   OpenStack Identity API v2 is deprecated in\n")
        out_file.write("   the Mitaka release and later.\n\n")
        out_file.write("   You can select the Identity API version to use\n")
        out_file.write("   by adding the\n")
        out_file.write("   :option:`--os-identity-api-version`\n")
        out_file.write("   parameter or by setting the corresponding\n")
        out_file.write("   environment variable:\n\n")

        out_file.write("   .. code-block:: console\n\n")
        out_file.write("      export OS_IDENTITY_API_VERSION=3\n\n")

        extra_params = ["--os-auth-type", "token"]
        subcommands = discover_subcommands(os_command, subcommands,
                                           extra_params)
        generate_subcommands(os_command, out_file, subcommands,
                             extra_params, "", "")
    elif os_command == 'glance':
        format_heading("Image service API v2 commands", 2, out_file)

    discover_and_generate_subcommands(os_command, out_file, subcommands,
                                      None, "", "")

    # Print subcommands for different API versions
    if os_command == 'cinder':
        out_file.write("\n")
        format_heading("Block Storage API v1 commands (DEPRECATED)",
                       2, out_file)

        discover_and_generate_subcommands(os_command, out_file, subcommands,
                                          None, "_v1", " (v1)")
    if os_command == 'glance':
        out_file.write("\n")
        format_heading("Image service API v1 commands", 2, out_file)
        out_file.write("As of this version, the default API version is 2.\n")
        out_file.write("You can select an API version to use by adding the\n")
        out_file.write(":option:`--os-image-api-version` parameter or by\n")
        out_file.write("setting the corresponding environment variable:\n\n")

        out_file.write(".. code-block:: console\n\n")
        out_file.write("   export OS_IMAGE_API_VERSION=1\n\n")
        discover_and_generate_subcommands(os_command, out_file, subcommands,
                                          ["--os-image-api-version", "1"],
                                          "_v1", " (v1)")

    print("Finished.\n")
    out_file.close()
    return True


def main():
    clients = get_clients()
    api_clients = sorted([x for x in clients if not x.endswith('-manage')])
    manage_clients = sorted([x for x in clients if x.endswith('-manage')])
    all_clients = api_clients + manage_clients

    parser = argparse.ArgumentParser(description="Generate RST files "
                                     "to document python-PROJECTclients.")
    parser.add_argument('clients', metavar='client', nargs='*',
                        help="OpenStack command to document. Specify "
                        "multiple times to generate documentation for "
                        "multiple clients. One of: " +
                        ", ".join(all_clients) + ".")
    parser.add_argument("--all", help="Document all clients. "
                        "Namely " + ", ".join(all_clients) + ".",
                        action="store_true")
    parser.add_argument("--all-api", help="Document all API clients. "
                        "Namely " + ", ".join(clients.keys()) + ".",
                        action="store_true")
    parser.add_argument("--all-manage", help="Document all manage clients. "
                        "Namely " + ", ".join(manage_clients) + ".",
                        action="store_true")
    parser.add_argument("--output-dir", default=".",
                        help="Directory to write generated files to")
    parser.add_argument("--continue-on-error", default=False,
                        help="Continue with remaining clients even if an "
                        "error occurs generating a client file.",
                        action="store_true")
    parser.add_argument("--version", default=False,
                        help="Show program's version number and exit.",
                        action="store_true")
    prog_args = parser.parse_args()

    client_list = []
    if prog_args.all or prog_args.all_api or prog_args.all_manage:
        if prog_args.all or prog_args.all_api:
            client_list = api_clients
        if prog_args.all or prog_args.all_manage:
            client_list.extend(manage_clients)
    elif prog_args.clients:
        client_list = prog_args.clients

    if not prog_args or 'help' in [client.lower() for client in client_list]:
        parser.print_help()
        sys.exit(0)
    elif prog_args.version:
        print(os_doc_tools.__version__)
        sys.exit(0)

    if not client_list:
        parser.print_help()
        sys.exit(1)

    print("OpenStack Auto Documenting of Commands (using "
          "openstack-doc-tools version %s)\n"
          % os_doc_tools.__version__)

    success_list = []
    error_list = []
    for client in client_list:
        if document_single_project(
                client, prog_args.output_dir, prog_args.continue_on_error):
            success_list.append(client)
        else:
            error_list.append(client)

    if success_list:
        print("Generated documentation for: %s" % ", ".join(success_list))
    if error_list:
        print("Generation failed for: %s" % ", ".join(error_list))
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
