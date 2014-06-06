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

# -----------------------------------------------------------------------------
# Public interface
# -----------------------------------------------------------------------------


def check_syntax(path):
    """Check syntax of one JSON file."""
    _process_file(path)


def check_formatting(path):
    """Check formatting of one JSON file."""
    _process_file(path, formatting='check')


def fix_formatting(path):
    """Fix formatting of one JSON file."""
    _process_file(path, formatting='fix')

# -----------------------------------------------------------------------------
# Implementation details
# -----------------------------------------------------------------------------


def _indent_note(errstr):
    """Indents and wraps a string."""
    return textwrap.fill(errstr, initial_indent=8 * ' ',
                         subsequent_indent=12 * ' ',
                         width=80)


def _get_demjson_diagnostics(raw):
    """Get diagnostics string for invalid JSON files from demjson."""
    errstr = None
    try:
        demjson.decode(raw, strict=True)
    except demjson.JSONError as err:
        errstr = err.pretty_description()
    return errstr


class ParserException(Exception):
    pass


def _parse_json(raw):
    """Parse raw JSON file."""
    try:
        parsed = json.loads(raw, object_pairs_hook=collections.OrderedDict)
    except ValueError as err:
        note = _indent_note(str(err))
        # if demjson is available, print its diagnostic string as well
        if demjson:
            demerr = _get_demjson_diagnostics(raw)
            if demerr:
                note += "\n" + _indent_note(demerr)
        raise ParserException(note)
    else:
        return parsed


def _format_parsed_json(parsed):
    """Pretty-print JSON file content while retaining key order."""
    return json.dumps(parsed, sort_keys=False, separators=(',', ': '),
                      indent=4)


def _process_file(path, formatting=None):
    """Check syntax/formatting and fix formatting of a JSON file.

    :param formatting: one of 'check' or 'fix'
    """
    with open(path, 'r') as infile:
        raw = infile.read()
        try:
            parsed = _parse_json(raw)
        except ParserException as err:
            print("%s\n%s" % (path, err))
        else:
            if formatting in ('check', 'fix'):
                formatted = _format_parsed_json(parsed)
                if formatted != raw:
                    if formatting == "fix":
                        with open(path, 'w') as outfile:
                            outfile.write(formatted)
                        errstr = _indent_note("Reformatted")
                    else:
                        errstr = _indent_note("Reformatting needed")
                    print("%s\n%s" % (path, errstr))
            else:
                # for the benefit of external callers
                return ValueError("formatting arg must be 'check' or 'fix'")


def main():
    parser = argparse.ArgumentParser(description="Validate and reformat JSON"
                                     "files.")
    parser.add_argument('files', metavar='FILES', nargs='+')
    parser.add_argument('-f', '--formatting', choices=['check', 'fix'],
                        help='check or fix formatting of JSON files')
    args = parser.parse_args()

    for path in args.files:
        _process_file(path, args.formatting)

if __name__ == "__main__":
    sys.exit(main())
