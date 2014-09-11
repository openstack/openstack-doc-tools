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
import subprocess
import sys

import os_doc_tools
from os_doc_tools.common import check_output   # noqa


def use_help_flag(os_command):
    """Use --help flag (instead of help keyword)

    Returns true if the command requires a --help flag instead
    of a help keyword.
    """

    return os_command == "swift" or "-manage" in os_command


def quote_xml(line):
    """Convert special characters for XML output."""

    line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    if 'DEPRECATED!' in line:
        line = line.replace('DEPRECATED!', '<emphasis>DEPRECATED!</emphasis>')
    elif 'DEPRECATED' in line:
        line = line.replace('DEPRECATED', '<emphasis>DEPRECATED</emphasis>')

    if 'env[' in line:
        line = line.replace('env[', '<code>env[').replace(']', ']</code>')

    return line


def generate_heading(os_command, api_name, title, os_file):
    """Write DocBook file header.

    :param os_command: client command to document
    :param api_name:   string description of the API of os_command
    :param os_file:    open filehandle for output of DocBook file
    """

    try:
        version = check_output([os_command, "--version"],
                               stderr=subprocess.STDOUT)
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            print("Command %s not found, aborting." % os_command)
            sys.exit(1)
    # Extract version from "swift 0.3"
    version = version.strip().rpartition(' ')[2]

    print("Documenting '%s help (version %s)'" % (os_command, version))

    if use_help_flag(os_command):
        help_str = "<replaceable>COMMAND</replaceable> <option>--help</option>"
    else:
        help_str = "<option>help</option> <replaceable>COMMAND</replaceable>"

    header1 = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<chapter xmlns=\"http://docbook.org/ns/docbook\"
  xmlns:xi=\"http://www.w3.org/2001/XInclude\"
  xmlns:xlink=\"http://www.w3.org/1999/xlink\"
  version=\"5.0\"
  xml:id=\"%(os_command)sclient_commands\">

    <!-- This file is automatically generated, do not edit -->

    <?dbhtml stop-chunking?>

    <title>%(title)s</title>\n"""
    if os_command == "openstack":
        header2 = """
    <para>The <command>%(os_command)s</command> client is a common
       OpenStack command-line interface (CLI).\n"""
    else:
        header2 = """
    <para>The <command>%(os_command)s</command> client is the command-line
        interface (CLI) for the %(api_name)s and its extensions.\n"""

    header3 = """
       This chapter documents <command>%(os_command)s</command> version
        <literal>%(version)s</literal>.
    </para>

    <para>For help on a specific <command>%(os_command)s</command>
       command, enter:
    </para>
    <screen><prompt>$</prompt> <userinput><command>%(os_command)s</command> \
%(help_str)s</userinput></screen>

    <section xml:id=\"%(os_command)sclient_command_usage\">
       <title>%(os_command)s usage</title>\n"""

    format_dict = {
        "os_command": os_command,
        "api_name": api_name,
        "title": title,
        "version": version,
        "help_str": help_str
    }
    os_file.write(header1 % format_dict)
    os_file.write(header2 % format_dict)
    os_file.write(header3 % format_dict)


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
    # 1. --version
    # 2. --timeout <seconds>
    # 3. --service <service>, --service-id <service>
    # 4. -v, --verbose
    # 5. -p PORT, --port PORT
    # 6. <backup>              ID of the backup to restore.
    # 7. --alarm-action <Webhook URL>
    # 8.   <NAME or ID>  Name or ID of stack to resume.

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

        while len(words) > 1:
            if words[1].startswith('DEPRECATED'):
                break
            if last_was_option:
                if (words[1].startswith(("-", '<', '{', '[')) or
                   is_option(words[1])):
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
        if len(words) > 0:
            w1 = words[0]
            del words[0]
            for w in words:
                w1 += " " + w

        if len(w1) == 0:
            split_line = [w0]
        else:
            split_line = [w0, w1]
    else:
        split_line = line.split(None, 1)

    return split_line


def format_table(title, lines, os_file):
    """Nicely print section of lines."""

    close_entry = False
    os_file.write("  <variablelist wordsize=\"10\">\n")
    if len(title) > 0:
        os_file.write("    <title>%s</title>\n" % title)

    for line in lines:
        if len(line) == 0 or line[0] != ' ':
            break
        # We have to handle these cases:
        # 1. command  Explanation
        # 2. command
        #             Explanation on next line
        # 3. command  Explanation continued
        #             on next line
        # If there are more than 8 spaces, let's treat it as
        # explanation.
        if line.startswith('        '):
            # Explanation
            os_file.write("      %s\n" % quote_xml(line.lstrip(' ')))
            continue
        # Now we have a command or parameter to handle
        split_line = extract_options(line)

        if not close_entry:
            close_entry = True
        else:
            os_file.write("      </para>\n")
            os_file.write("    </listitem>\n")
            os_file.write("  </varlistentry>\n")

        os_file.write("  <varlistentry>\n")
        os_file.write("    <term><command>%s</command></term>\n"
                      % quote_xml(split_line[0]))
        os_file.write("    <listitem>\n")
        os_file.write("      <para>\n")
        if len(split_line) > 1:
            os_file.write("        %s\n" % quote_xml(split_line[1]))

    os_file.write("      </para>\n")
    os_file.write("    </listitem>\n")
    os_file.write("  </varlistentry>\n")
    os_file.write(" </variablelist>\n")

    return


def generate_command(os_command, os_file):
    """Convert os_command --help to DocBook.

    :param os_command: client command to document
    :param os_file:    open filehandle for output of DocBook file
    """

    help_lines = check_output([os_command, "--help"]).split('\n')

    ignore_next_lines = False
    next_line_screen = True
    next_line_screen = True
    line_index = -1
    in_screen = False
    for line in help_lines:
        line_index += 1
        xline = quote_xml(line)
        if len(line) > 0 and line[0] != ' ':
            # XXX: Might have whitespace before!!
            if '<subcommands>' in line:
                ignore_next_lines = False
                continue
            if 'Positional arguments' in line:
                ignore_next_lines = True
                next_line_screen = True
                os_file.write("</computeroutput></screen>\n")
                in_screen = False
                format_table('Subcommands', help_lines[line_index + 2:],
                             os_file)
                continue
            if line.startswith(('Optional arguments:', 'Optional:',
                                'Options:', 'optional arguments')):
                if in_screen:
                    os_file.write("</computeroutput></screen>\n")
                    in_screen = False
                os_file.write("    </section>\n")
                os_file.write("    <section ")
                os_file.write("xml:id=\"%sclient_command_optional\">\n"
                              % os_command)
                os_file.write("        <title>%s optional arguments</title>\n"
                              % os_command)
                format_table('', help_lines[line_index + 1:],
                             os_file)
                next_line_screen = True
                ignore_next_lines = True
                continue
            # neutron
            if line.startswith('Commands for API v2.0:'):
                if in_screen:
                    os_file.write("</computeroutput></screen>\n")
                    in_screen = False
                os_file.write("    </section>\n")
                os_file.write("    <section ")
                os_file.write("xml:id=\"%sclient_command_api_2_0\">\n"
                              % os_command)
                os_file.write("        <title>%s API v2.0 commands</title>\n"
                              % os_command)
                format_table('', help_lines[line_index + 1:],
                             os_file)
                next_line_screen = True
                ignore_next_lines = True
                continue
            # swift
            if line.startswith('Examples:'):
                os_file.write("    </section>\n")
                os_file.write("    <section ")
                os_file.write("xml:id=\"%sclient_command_examples\">\n"
                              % os_command)
                os_file.write("        <title>%s examples</title>\n"
                              % os_command)
                next_line_screen = True
                ignore_next_lines = False
                continue
            if not line.startswith('usage'):
                continue
        if not ignore_next_lines:
            if next_line_screen:
                os_file.write("        <screen><computeroutput>%s" % xline)
                next_line_screen = False
                in_screen = True
            elif len(line) > 0:
                os_file.write("\n%s" % xline.rstrip())

    if in_screen:
        os_file.write("</computeroutput></screen>\n")

    os_file.write("    </section>\n")


def generate_subcommand(os_command, os_subcommand, os_file, extra_params,
                        suffix, title_suffix):
    """Convert os_command help os_subcommand to DocBook.

    :param os_command: client command to document
    :param os_subcommand: client subcommand to document
    :param os_file:    open filehandle for output of DocBook file
    :param extra_params: Extra parameter to pass to os_command
    :param suffix: Extra suffix to add to xml:id
    :param title_suffix: Extra suffix for title
    """

    args = [os_command]
    if extra_params:
        args.extend(extra_params)
    if use_help_flag(os_command):
        args.append(os_subcommand)
        args.append("--help")
    else:
        args.append("help")
        args.append(os_subcommand)
    help_lines = check_output(args).split('\n')

    os_subcommandid = os_subcommand.replace(' ', '_')
    os_file.write("    <section xml:id=\"%sclient_subcommand_%s%s\">\n"
                  % (os_command, os_subcommandid, suffix))
    os_file.write("        <title>%s %s%s</title>\n"
                  % (os_command, os_subcommand, title_suffix))

    if os_command == "swift":
        next_line_screen = False
        os_file.write("\n        <screen><computeroutput>Usage: swift %s"
                      "</computeroutput></screen>"
                      % (os_subcommand))
        os_file.write("\n        <para>")
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
                os_file.write("\n        </para>")
            if line.startswith(('Positional arguments',
                                'positional arguments')):
                format_table('Positional arguments',
                             help_lines[line_index + 1:], os_file)
                skip_lines = True
                continue
            elif line.startswith(('Optional arguments:',
                                  'optional arguments')):
                format_table('Optional arguments',
                             help_lines[line_index + 1:], os_file)
                break
            else:
                format_table('Arguments', help_lines[line_index + 1:], os_file)
                break
        if skip_lines:
            continue
        if len(line) == 0:
            if not in_para:
                os_file.write("</computeroutput></screen>")
                os_file.write("\n        <para>")
            in_para = True
            continue
        xline = quote_xml(line)
        if next_line_screen:
            os_file.write("        <screen><computeroutput>%s" % xline)
            next_line_screen = False
        else:
            os_file.write("\n%s" % (xline))

    if in_para:
        os_file.write("\n        </para>\n")
    os_file.write("    </section>\n")


def generate_subcommands(os_command, os_file, blacklist, only_subcommands,
                         extra_params, suffix, title_suffix):
    """Convert os_command help subcommands for all subcommands to DocBook.

    :param os_command: client command to document
    :param os_file:    open filehandle for output of DocBook file
    :param blacklist:  list of elements that will not be documented
    :param only_subcommands: if not empty, list of subcommands to document
    :param extra_params: Extra parameter to pass to os_command.
    :param suffix: Extra suffix to add to xml:id
    :param title_suffix: Extra suffix for title
    """

    print("Documenting '%s' subcommands..." % os_command)
    blacklist.append("bash-completion")
    blacklist.append("complete")
    blacklist.append("help")
    if not only_subcommands:
        all_options = check_output([os_command,
                                    "bash-completion"]).strip().split()
    else:
        all_options = only_subcommands

    subcommands = [o for o in all_options if not
                   (o.startswith('-') or o in blacklist)]
    for subcommand in sorted(subcommands):
        generate_subcommand(os_command, subcommand, os_file, extra_params,
                            suffix, title_suffix)
    print ("%d subcommands documented." % len(subcommands))


def generate_end(os_file):
    """Finish writing file.

    :param os_file:    open filehandle for output of DocBook file
    """

    print("Finished.\n")
    os_file.write("</chapter>\n")


def get_openstack_subcommands(commands):
    """Get all subcommands of 'openstack' without using bashcompletion."""
    subcommands = []
    for command in commands:
        output = check_output(["openstack", "help", command])
        for line in output.split("\n"):
            if line.strip().startswith(command):
                subcommands.append(line.strip())

    return subcommands


def document_single_project(os_command, output_dir):
    """Create documenation for os_command."""

    print ("Documenting '%s'" % os_command)

    blacklist = []
    subcommands = []
    if os_command == 'ceilometer':
        api_name = "Telemetry API"
        title = "Telemetry command-line client"
        blacklist = ["alarm-create"]
    elif os_command == 'cinder':
        api_name = "OpenStack Block Storage API"
        title = "Block Storage command-line client"
    elif os_command == 'glance':
        api_name = 'OpenStack Image Service API'
        title = "Image Service command-line client"
        # Does not know about bash-completion yet, need to specify
        # subcommands manually
        subcommands = ["image-create", "image-delete", "image-list",
                       "image-show", "image-update", "member-create",
                       "member-delete", "member-list"]
    elif os_command == 'heat':
        api_name = "Orchestration API"
        title = "Orchestration command-line client"
        blacklist = ["create", "delete", "describe", "event",
                     "gettemplate", "list", "resource",
                     "update", "validate"]
    elif os_command == 'ironic':
        api_name = "Bare metal"
        title = "Bare metal command-line client"
    elif os_command == 'keystone':
        api_name = "OpenStack Identity API"
        title = "Identity service command-line client"
    elif os_command == 'neutron':
        api_name = "OpenStack Networking API"
        title = "Networking command-line client"
    elif os_command == 'nova':
        api_name = "OpenStack Compute API"
        title = "Compute command-line client"
        blacklist = ["add-floating-ip", "remove-floating-ip"]
    elif os_command == 'sahara':
        api_name = "Data processing API"
        title = "Data processing command-line client"
    elif os_command == 'swift':
        api_name = "OpenStack Object Storage API"
        title = "Object Storage command-line client"
        # Does not know about bash-completion yet, need to specify
        # subcommands manually
        subcommands = ["delete", "download", "list", "post",
                       "stat", "upload"]
    elif os_command == 'trove':
        api_name = "Database API"
        title = "Database Service command-line client"
        blacklist = ["resize-flavor"]
    elif os_command == 'trove-manage':
        api_name = "Database Management Utility"
        title = "Database Service Management command-line client"
        # Does not know about bash-completion yet, need to specify
        # subcommands manually
        subcommands = ["db_sync", "db_upgrade",
                       "db_downgrade", "datastore_update",
                       "datastore_version_update", "db_recreate"]
    elif os_command == 'openstack':
        api_name = ''
        title = "OpenStack client"
        # Does not know about bash-completion yet, need to specify
        # commands manually and to fetch subcommands automatically
        commands = ["aggregate", "backup", "compute", "console", "container",
                    "ec2", "endpoint", "extension", "flavor", "host",
                    "hypervisor", "image", "ip", "keypair", "limits", "module",
                    "network", "object", "project", "quota", "role",
                    "security", "server", "service", "snapshot", "token",
                    "user", "volume"]
        subcommands = get_openstack_subcommands(commands)
    else:
        print("'%s' command not yet handled" % os_command)
        sys.exit(-1)

    out_filename = "ch_cli_" + os_command + "_commands.xml"
    out_file = open(os.path.join(output_dir, out_filename), 'w')
    generate_heading(os_command, api_name, title, out_file)
    generate_command(os_command, out_file)

    if os_command == 'glance':
        out_file.write("""
    <section xml:id=\"glance_cli_v1\">
       <title>Image Service API v1 commands</title>\n""")

    generate_subcommands(os_command, out_file, blacklist,
                         subcommands, None, "", "")

    if os_command == 'glance':
        out_file.write("    </section>\n")
        subcommands = ['explain', 'image-create', 'image-delete',
                       'image-download', 'image-list', 'image-show',
                       'image-tag-delete', 'image-tag-update', 'image-update',
                       'image-upload', 'location-add', 'location-delete',
                       'location-update', 'md-namespace-create',
                       'md-namespace-delete', 'md-namespace-import',
                       'md-namespace-list', 'md-namespace-objects-delete',
                       'md-namespace-properties-delete',
                       'md-namespace-resource-type-list', 'md-namespace-show',
                       'md-namespace-update', 'md-object-create',
                       'md-object-delete', 'md-object-list',
                       'md-object-property-show', 'md-object-show',
                       'md-object-update', 'md-property-create',
                       'md-property-delete', 'md-property-list',
                       'md-property-show', 'md-property-update',
                       'md-resource-type-associate',
                       'md-resource-type-deassociate',
                       'md-resource-type-list', 'member-create',
                       'member-delete', 'member-list', 'member-update']

        out_file.write("""
    <section xml:id=\"glance_cli_v2\">
       <title>Image Service API v2 commands</title>
    <para>
       You can select an API version to use by adding the
       <parameter>--os-image-api-version</parameter> option or by setting
       the corresponding environment variable:\n""")
        out_file.write("<screen><prompt>$</prompt> <userinput>"
                       "export OS_IMAGE_API_VERSION=2</userinput></screen>\n"
                       "</para>\n")

        generate_subcommands(os_command, out_file, blacklist,
                             subcommands, ["--os-image-api-version", "2"],
                             "_v2", " (v2)")
        out_file.write("    </section>\n")

    generate_end(out_file)
    out_file.close()


def main():
    print("OpenStack Auto Documenting of Commands (using "
          "openstack-doc-tools version %s)\n"
          % os_doc_tools.__version__)

    api_clients = ["ceilometer", "cinder", "glance", "heat", "keystone",
                   "nova", "neutron", "openstack", "swift", "trove"]
    manage_clients = ["trove-manage"]
    all_clients = api_clients + manage_clients

    parser = argparse.ArgumentParser(description="Generate DocBook XML files "
                                     "to document python-PROJECTclients.")
    parser.add_argument('client', nargs='?',
                        help="OpenStack command to document. One of: " +
                        ", ".join(all_clients) + ".")
    parser.add_argument("--all", help="Document all clients. "
                        "Namely " + ", ".join(all_clients) + ".",
                        action="store_true")
    parser.add_argument("--all-api", help="Document all API clients. "
                        "Namely " + ", ".join(api_clients) + ".",
                        action="store_true")
    parser.add_argument("--all-manage", help="Document all manage clients. "
                        "Namely " + ", ".join(manage_clients) + ".",
                        action="store_true")
    parser.add_argument("--output-dir", default=".",
                        help="Directory to write generated files to")
    prog_args = parser.parse_args()

    if prog_args.all or prog_args.all_api or prog_args.all_manage:
        if prog_args.all or prog_args.all_api:
            for client in api_clients:
                document_single_project(client, prog_args.output_dir)
        if prog_args.all or prog_args.all_manage:
            for client in manage_clients:
                document_single_project(client, prog_args.output_dir)
    elif prog_args.client is None:
        parser.print_help()
        sys.exit(1)
    else:
        document_single_project(prog_args.client, prog_args.output_dir)


if __name__ == "__main__":
    sys.exit(main())
