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

# Must import this before argparse
import oslo.config   # NOQA

import argparse
import sys

import common    # NOQA

# this is for the internationalisation function in gettext
import __builtin__
__builtin__.__dict__['_'] = lambda x: x


def main():
    parser = argparse.ArgumentParser(
        description='Manage flag files, to aid in updating documentation.',
        usage='%(prog)s <cmd> <package> [options]')
    parser.add_argument('subcommand',
                        help='action (create, update, verify) [REQUIRED]',
                        choices=['create', 'update', 'docbook'])
    parser.add_argument('package',
                        help='name of the top-level package')
    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        dest='verbose',
                        required=False,)
    parser.add_argument('-i', '--input',
                        dest='repo',
                        help='path to valid git repository [REQUIRED]',
                        required=True,
                        type=str,)
    args = parser.parse_args()

    package_name = common.git_check(args.repo)

    sys.path.insert(0, args.repo)
    try:
        __import__(package_name)
    except ImportError as e:
        if args.verbose >= 1:
            print(str(e))
            print("Failed to import: %s (%s)" % (package_name, e))

    modules = common.import_modules(args.repo, package_name,
                                    verbose=args.verbose)
    options = common.OptionsCache(modules, verbose=args.verbose)

    if args.verbose > 0:
        print("%s options imported from package %s." % (len(options),
                                                        str(package_name)))

    if args.subcommand == 'create':
        common.create_flagmappings(package_name, options, verbose=args.verbose)
        return

    if args.subcommand == 'update':
        common.update_flagmappings(package_name, options, verbose=args.verbose)
        return

    if args.subcommand == 'docbook':
        common.write_docbook(package_name, options, verbose=args.verbose)
        return


if __name__ == "__main__":
    main()
