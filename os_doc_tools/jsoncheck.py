#!/usr/bin/env python

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""

Usage:
    jsoncheck.py [-f] FILES

Checks JSON syntax and optionally reformats (pretty-prints) the valid files.

Optional:
    - demjson Python library (better diagnostics for invalid JSON synax)

"""

from __future__ import print_function

import argparse
import collections
import json
import sys
import textwrap

try:
    import demjson
except ImportError:
    demjson = None
    sys.stderr.write("Cannot import the demjson Python module. Diagnostics "
                     "for invalid JSON files\nwill be limited.\n")


def indent_note(errstr):
    """Indents and wraps a string."""
    return textwrap.fill(errstr, initial_indent=8 * ' ',
                         subsequent_indent=12 * ' ',
                         width=80)


def get_demjson_diagnostics(raw):
    """Get diagnostics string for invalid JSON files from demjson."""
    errstr = None
    try:
        demjson.decode(raw, strict=True)
    except demjson.JSONError as err:
        errstr = err.pretty_description()
    return errstr


class ParserException(Exception):
    pass


def parse_json(raw):
    """Parse raw JSON file."""
    try:
        parsed = json.loads(raw, object_pairs_hook=collections.OrderedDict)
    except ValueError as err:
        note = indent_note(str(err))
        # if demjson is available, print its diagnostic string as well
        if demjson:
            demerr = get_demjson_diagnostics(raw)
            if demerr:
                note += "\n" + indent_note(demerr)
        raise ParserException(note)
    else:
        return parsed


class FormattingException(Exception):
    pass


def check_format(parsed, raw, path=None):
    """Check formatting; pretty-print JSON file while retaining key order."""
    formatted = json.dumps(parsed, sort_keys=False, separators=(',', ': '),
                           indent=4)
    if formatted != raw:
        if path:
            with open(path, 'w') as outfile:
                outfile.write(formatted)
            errstr = indent_note("Reformatted")
        else:
            errstr = indent_note("Reformatting needed")
        raise FormattingException(errstr)


def main():
    parser = argparse.ArgumentParser(description="Validate and reformat JSON"
                                     "files.")
    parser.add_argument('files', metavar='FILES', nargs='+')
    parser.add_argument('-f', '--format', action='store_true',
                        help='reformat valid JSON files')
    args = parser.parse_args()

    for path in args.files:
        with open(path, 'r') as infile:
            raw = infile.read()
            infile.close()
            try:
                parsed = parse_json(raw)
            except ParserException as err:
                print("%s\n%s" % (path, err))
            else:
                try:
                    check_format(parsed, raw, path if args.format else None)
                except FormattingException as err:
                    print("%s\n%s" % (path, err))


if __name__ == "__main__":
    sys.exit(main())
