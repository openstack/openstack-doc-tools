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
import yaml

import os_doc_tools

DEVNULL = open(os.devnull, 'wb')


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
        version = subprocess.check_output([os_command, "--version"],
                                          stderr=subprocess.STDOUT)
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            print("Command %s not found, aborting." % os_command)
            sys.exit(1)
    # Extract version from "swift 0.3"
    version = version.splitlines()[-1].strip().rpartition(' ')[2]

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

    if os_command == "keystone":
        header_deprecation = """
    <warning>
        <para>The %(os_command)s CLI is deprecated in favor of
            python-openstackclient. For a Python library, continue using
            python-%(os_command)sclient.</para>
    </warning>\n"""
    else:
        header_deprecation = None

    format_dict = {
        "os_command": os_command,
        "api_name": api_name,
        "title": title,
        "version": version,
        "help_str": help_str
    }
    os_file.write(header1 % format_dict)
    if header_deprecation:
        os_file.write(header_deprecation % format_dict)
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

    help_lines = subprocess.check_output([os_command, "--help"],
                                         stderr=DEVNULL).split('\n')

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
            # sahara
            if line.startswith('Common auth options'):
                if in_screen:
                    os_file.write("</computeroutput></screen>\n")
                    in_screen = False
                os_file.write("    </section>\n")
                os_file.write("    <section ")
                os_file.write("xml:id=\"%sclient_command_common_auth\">\n"
                              % os_command)
                os_file.write("        <title>%s common authentication "
                              "arguments</title>\n"
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
    help_lines = subprocess.check_output(args, stderr=DEVNULL)

    if 'positional arguments' in help_lines.lower():
        index = help_lines.lower().index('positional arguments')
    else:
        index = len(help_lines)

    if 'deprecated' in (help_lines[0:index].lower()):
        print("Subcommand '%s' is deprecated, skipping." % os_subcommand)
        return

    help_lines = help_lines.split('\n')

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


def generate_subcommands(os_command, os_file, subcommands, extra_params,
                         suffix, title_suffix):
    """Convert os_command help subcommands for all subcommands to DocBook.

    :param os_command: client command to document
    :param os_file:    open filehandle for output of DocBook file
    :param subcommands: list or type ('complete' or 'bash-completion')
                        of subcommands to document
    :param extra_params: Extra parameter to pass to os_command.
    :param suffix: Extra suffix to add to xml:id
    :param title_suffix: Extra suffix for title
    """

    print("Documenting '%s' subcommands..." % os_command)
    blacklist = ['bash-completion', 'complete', 'help']
    if type(subcommands) is str:
        args = [os_command]
        if extra_params:
            args.extend(extra_params)
        if subcommands == 'complete':
            subcommands = []
            args.append('complete')
            for line in [x.strip() for x in
                         subprocess.check_output(args).split('\n')
                         if x.strip().startswith('cmds_') and '-' in x]:
                subcommand, _ = line.split('=')
                subcommand = subcommand.replace('cmds_', '').replace('_', ' ')
                subcommands.append(subcommand)
        else:
            args.append('bash-completion')
            subcommands = subprocess.check_output(args).strip().split()

    subcommands = sorted([o for o in subcommands if not (o.startswith('-') or
                                                         o in blacklist)])
    for subcommand in subcommands:
        generate_subcommand(os_command, subcommand, os_file, extra_params,
                            suffix, title_suffix)
    print ("%d subcommands documented." % len(subcommands))


def generate_end(os_file):
    """Finish writing file.

    :param os_file:    open filehandle for output of DocBook file
    """

    print("Finished.\n")
    os_file.write("</chapter>\n")


def get_clients():
    """Load client definitions from the resource file."""
    fname = os.path.join(os.path.dirname(__file__),
                         'resources/clients.yaml')
    clients = yaml.load(open(fname, 'r'))
    return clients


def document_single_project(os_command, output_dir):
    """Create documenation for os_command."""

    clients = get_clients()

    if os_command not in clients:
        print("'%s' command not yet handled" % os_command)
        sys.exit(-1)

    print ("Documenting '%s'" % os_command)

    data = clients[os_command]
    if 'name' in data:
        api_name = "%s API" % data['name']
        title = "%s command-line client" % data.get('title', data['name'])
    else:
        api_name = ''
        title = data.get('title', '')
    subcommands = data.get('subcommands', 'bash-completion')

    out_filename = "ch_cli_" + os_command + "_commands.xml"
    out_file = open(os.path.join(output_dir, out_filename), 'w')
    generate_heading(os_command, api_name, title, out_file)
    generate_command(os_command, out_file)

    if os_command == 'cinder':
        out_file.write("""
    <section xml:id=\"cinder_cli_v1\">
       <title>Block Storage API v1 commands</title>\n""")
    if os_command == 'glance':
        out_file.write("""
    <section xml:id=\"glance_cli_v1\">
       <title>Image service API v1 commands</title>\n""")
    if os_command == 'murano':
        out_file.write("""
    <section xml:id=\"murano_cli_v1\">
       <title>Application catalog API v1 commands</title>\n""")
    if os_command == 'openstack':
        generate_subcommands(os_command, out_file, subcommands,
                             ["--os-auth-type", "token"], "", "")
    else:
        generate_subcommands(os_command, out_file, subcommands, None, "", "")

    if os_command == 'cinder':
        out_file.write("    </section>\n")
        out_file.write("""
    <section xml:id=\"cinder_cli_v2\">
       <title>Block Storage API v2 commands</title>
    <para>
       You can select an API version to use by adding the
       <parameter>--os-volume-api-version</parameter> parameter or by setting
       the corresponding environment variable:\n""")
        out_file.write("<screen><prompt>$</prompt> <userinput>"
                       "export OS_VOLUME_API_VERSION=2</userinput></screen>\n"
                       "</para>\n")

        generate_subcommands(os_command, out_file, subcommands,
                             ["--os-volume-api-version", "2"], "_v2", " (v2)")
        out_file.write("    </section>\n")
    if os_command == 'glance':
        out_file.write("""
    </section>\n
    <section xml:id=\"glance_cli_v2\">
       <title>Image service API v2 commands</title>
    <para>
       You can select an API version to use by adding the
       <parameter>--os-image-api-version</parameter> parameter or by setting
       the corresponding environment variable:\n""")
        out_file.write("<screen><prompt>$</prompt> <userinput>"
                       "export OS_IMAGE_API_VERSION=2</userinput></screen>\n"
                       "</para>\n")

        generate_subcommands(os_command, out_file, subcommands,
                             ["--os-image-api-version", "2"], "_v2", " (v2)")
        out_file.write("    </section>\n")

    generate_end(out_file)
    out_file.close()


def main():
    print("OpenStack Auto Documenting of Commands (using "
          "openstack-doc-tools version %s)\n"
          % os_doc_tools.__version__)

    clients = get_clients()
    api_clients = sorted([x for x in clients if not x.endswith('-manage')])
    manage_clients = sorted([x for x in clients if x.endswith('-manage')])
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
                        "Namely " + ", ".join(clients.keys()) + ".",
                        action="store_true")
    parser.add_argument("--all-manage", help="Document all manage clients. "
                        "Namely " + ", ".join(manage_clients) + ".",
                        action="store_true")
    parser.add_argument("--output-dir", default=".",
                        help="Directory to write generated files to")
    prog_args = parser.parse_args()

    if prog_args.all or prog_args.all_api or prog_args.all_manage:
        if prog_args.all or prog_args.all_api:
            for client in clients.keys():
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
