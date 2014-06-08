#!/usr/bin/env python

"""A script to prettify HTML and XML syntax.

Some examples of the prettified syntax are available
in the following changes:

* https://review.openstack.org/#/c/98652/
* https://review.openstack.org/#/c/98653/
* https://review.openstack.org/#/c/98655/
"""

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

# author: Christian Berendt <berendt@b1-systems.de>

from __future__ import print_function
import argparse
import sys

from bs4 import BeautifulSoup


def parse_command_line_arguments():
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-changes", action="store_true", default=False,
                        help="Write prettified XML or HTML syntax "
                             "back to file.")
    parser.add_argument("file", type=str, default=None,
                        help="A XML or HTML File to prettify.")
    return parser.parse_args()


def main():
    """Entry point for this script."""

    args = parse_command_line_arguments()

    try:
        soup = BeautifulSoup(open(args.file))
    except IOError as exception:
        print("ERROR: File '%s' could not be parsed: %s"
              % (args.file, exception))
        return 1

    if args.write_changes:
        try:
            with open(args.file, 'wb') as output:
                prettified = soup.prettify(encoding="utf8")
                output.write(prettified)
        except IOError as exception:
            print("ERROR: File '%s' could not be written: %s"
                  % (args.file, exception))
            return 1
    else:
        prettified = soup.prettify(encoding="utf8")
        print(prettified)

    return 0

if __name__ == '__main__':
    sys.exit(main())
