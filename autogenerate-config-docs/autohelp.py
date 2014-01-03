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

import common
import sys

# this is for the internationalisation function in gettext
import __builtin__
__builtin__.__dict__['_'] = lambda x: x



def main(action, file, format, repo, verbose=0, name=False, test=False):
    package_name = common.git_check(repo)

    sys.path.append(repo)
    try:
        __import__(package_name)
    except ImportError as e:
        if verbose >= 1:
            print str(e)
            print "Failed to import: %s (%s)" % (package_name, e)

    if verbose >= 1:
        flags = common.extract_flags(repo, package_name, verbose)
    else:
        flags = common.extract_flags(repo, package_name)

    print "%s flags imported from package %s." % (len(flags),
                                                  str(package_name))
    if action == "update":
        common.update(file, flags, True, verbose)
        return

    if format == "names":
        if verbose >= 1:
            common.write_flags(file, flags, True, verbose)
        else:
            common.write_flags(file, flags, True)

    if format == "docbook":
        groups = common.populate_groups(file)
        print "%s groups" % len(groups)
        if verbose >= 1:
            common.write_docbook('.', flags, groups, package_name, verbose)
        else:
            common.write_docbook('.', flags, groups, package_name)

    sys.exit(0)

if __name__ == "__main__":
    args = common.parse_me_args()
    main(args['action'],
         args['file'],
         args['format'],
         args['repo'],
         args['verbose'],
         args['name'],
         args['test'])
