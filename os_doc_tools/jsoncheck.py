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


def fix_formatting(path, verbose=False):
    """Fix formatting of one JSON file."""
    _process_file(path, formatting='fix', verbose=verbose)

# -----------------------------------------------------------------------------
# Implementation details
# -----------------------------------------------------------------------------


def _indent_note(note):
    """Indents and wraps a string."""
    indented_note = []
    # Split into single lines in case the argument is pre-formatted.
    for line in note.splitlines():
        indented_note.append(textwrap.fill(line, initial_indent=4 * ' ',
                             subsequent_indent=12 * ' ',
                             width=80))
    return "\n".join(indented_note)


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
        note = str(err)
        # if demjson is available, print its diagnostic string as well
        if demjson:
            demerr = _get_demjson_diagnostics(raw)
            if demerr:
                note += "\n" + demerr
        raise ParserException(note)
    else:
        return parsed


def _format_parsed_json(parsed):
    """Pretty-print JSON file content while retaining key order."""
    return json.dumps(parsed, sort_keys=False, separators=(',', ': '),
                      indent=4) + "\n"


def _process_file(path, formatting=None, verbose=False):
    """Check syntax/formatting and fix formatting of a JSON file.

    :param formatting: one of 'check' or 'fix' (default: None)

    Raises ValueError if JSON syntax is invalid or reformatting needed.
    """
    with open(path, 'r') as infile:
        raw = infile.read()
        try:
            parsed = _parse_json(raw)
        except ParserException as err:
            raise ValueError(err)
        else:
            if formatting in ('check', 'fix'):
                formatted = _format_parsed_json(parsed)
                if formatted != raw:
                    if formatting == "fix":
                        with open(path, 'w') as outfile:
                            outfile.write(formatted)
                        if verbose:
                            print("%s\n%s" % (path,
                                              _indent_note("Reformatted")))
                    else:
                        raise ValueError("Reformatting needed")
            elif formatting is not None:
                # for the benefit of external callers
                raise ValueError("Called with invalid formatting value.")


def main():
    parser = argparse.ArgumentParser(description="Validate and reformat JSON"
                                     "files.")
    parser.add_argument('files', metavar='FILES', nargs='+')
    parser.add_argument('-f', '--formatting', choices=['check', 'fix'],
                        help='check or fix formatting of JSON files')
    args = parser.parse_args()

    exit_status = 0
    for path in args.files:
        try:
            _process_file(path, args.formatting, verbose=True)
        except ValueError as err:
            print("%s\n%s" % (path, _indent_note(str(err))))
            exit_status = 1

    return exit_status

if __name__ == "__main__":
    sys.exit(main())
