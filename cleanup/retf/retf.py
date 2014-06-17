#!/usr/bin/env python

"""This script applies a set of regular expressions onto a set of files
to automatically identify and fix typographical errors.
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

# Based on the idea of 'Topy' written by Marti Raudsepp <marti@juffo.org>.
# Topy is available on Github at https://github.com/intgr/topy.

import argparse
import logging
import os
import shutil
import sys
import urllib2

from bs4 import BeautifulSoup
import glob2
import regex
import six
import yaml


class DownloadRetfListingFailed(Exception):
    """Exception for failed downloads of the RETF listing.

    Exception will be raised when the download of the RETF
    listing failed or the destination file could not be written.

    """

    pass


def download_listing(dest):
    """Download the latest RETF listing from Wikipedia."""
    logger = logging.getLogger('retf')
    try:
        url = ('https://en.wikipedia.org/wiki/Wikipedia:AutoWikiBrowser/'
               'Typos?action=raw')
        logger.debug("Downloading latest RETF listing from %s into %s.",
                     url, dest)
        response = urllib2.urlopen(url)
        data = response.read()
        logger.info("Downloading latest RETF listing from %s succeeded.", url)
    except urllib2.HTTPError as ex:
        raise DownloadRetfListingFailed(six.text_type(ex))
    except urllib2.URLError as ex:
        raise DownloadRetfListingFailed(six.text_type(ex))

    try:
        with open(dest, 'w+') as write:
            write.write(data)
        logger.info("Writing RETF listing to file %s succeeded.", dest)
    except IOError as ex:
        raise DownloadRetfListingFailed(six.text_type(ex))


def soupify_listing(src):
    """Parse a RETF listing."""
    return BeautifulSoup(open(src))


def generate_listing(src):
    """Compile all regular expressions in a RETF listing."""
    logger = logging.getLogger('retf')
    result = []

    soup = soupify_listing(src)

    for typo in soup.findAll('typo'):
        try:
            word = typo.attrs.get('word').encode('utf8')
            find = typo.attrs.get('find').encode('utf8')
            replace = typo.attrs.get('replace').encode('utf8')
            replace = replace.replace(b'$', b'\\')
        except AttributeError:
            continue

        # pylint: disable=W0703
        try:
            logger.debug("Compiling regular expression: %s.", find)
            compiled = regex.compile(find, flags=regex.V1)
        except Exception:
            logger.error("Compilation of regular expression %f failed.", find)
            continue
        # pylint: enable=W0703

        entry = {
            'description': word,
            'find': find,
            'replace': replace,
            'regex': compiled
        }

        result.append(entry)

    logger.debug("Compiled %d regular expression(s).", len(result))

    return result


def load_text_from_file(src):
    """Load content from a file."""
    logger = logging.getLogger('retf')
    logger.debug("Loading text from file %s.", src)
    with open(src, 'rb') as fpointer:
        text = fpointer.read()

    return text


def write_text_to_file(dest, text, no_backup, in_place):
    """Write content into a file."""
    logger = logging.getLogger('retf')

    if not no_backup:
        logger.debug("Copying %s to backup file %s.orig.", dest, dest)
        shutil.copy2(dest, "%s.orig" % dest)

    if not in_place:
        dest = "%s.retf" % dest

    logger.debug("Writing text to file %s.", dest)
    with open(dest, 'wb') as fpointer:
        fpointer.write(text)


def initialize_logging(debug, less_verbose):
    """Initialze the Logger."""
    logger = logging.getLogger(name='retf')
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.setLevel(logging.INFO)

    if less_verbose:
        logger.setLevel(logging.WARN)

    if debug:
        logger.setLevel(logging.DEBUG)

    return logging.getLogger('retf')


def parse_command_line_arguments():
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="Print debugging messages.",
                        action="store_true", default=False)
    parser.add_argument("--download", help="Download the latest RETF listing.",
                        action="store_true", default=False)
    parser.add_argument("--less-verbose", help="Be less verbose.",
                        action="store_true", default=False)
    parser.add_argument("--no-backup", help="Don't backup files.",
                        action="store_true", default=False)
    parser.add_argument("--in-place", help="Resolve found errors in place.",
                        action="store_true", default=False)
    parser.add_argument("--write-changes", action="store_true", default=False,
                        help="Write resolved findings back to files.")
    parser.add_argument("--disabled", type=str, default=None,
                        help="File containing the disabled rules.")
    parser.add_argument("--listing", help="File containing the RETF listing.",
                        type=str, default=os.path.join(
                            os.path.dirname(os.path.realpath(__file__)),
                            'retf.lst'))
    parser.add_argument("--path", type=str, nargs='*', default=[],
                        help="Path(s) that should be checked.")
    parser.add_argument("--extension", type=str, nargs='*', default=[],
                        help="Only check files with specified extension(s).")
    parser.add_argument("--file", nargs='*', type=str, default=[],
                        help="File(s) to check for typographical errors.")
    return (parser, parser.parse_args())


def load_disabled_rules(src):
    """Load disabled rules from YAML file."""
    logger = logging.getLogger('retf')
    listing = []

    if src:
        try:
            listing = yaml.load(open(src))
            for rule in listing:
                logger.debug("Rule '%s' is disabled.", rule)

        except IOError:
            logger.error("loading disabled rules from file %s failed", src)

    return listing


def get_file_listing(paths, files, extensions):
    """Generate listing with all files that should be check."""
    result = []
    if files:
        result += files

    # pylint: disable=E1101
    for path in paths:
        if extensions:
            for extension in extensions:
                result += glob2.glob("%s/**/*.%s" % (path, extension))
        else:
            result += glob2.glob("%s/**/*" % path)
    # pylint: enable=E1101

    return result


def check_file(src, rules, disabled):
    """Applies a set of rules on a file."""
    logger = logging.getLogger('retf')
    logger.info("Checking file %s for typographical errors.", src)
    content = load_text_from_file(src)
    findings = 0

    for rule in rules:
        if rule.get('description') in disabled:
            continue

        logger.debug("%s: checking rule '%s'.", src,
                     rule.get('description'))
        logger.debug(rule.get('find'))
        newcontent, count = rule.get('regex').subn(
            rule.get('replace'), content
        )

        if count > 0:
            logger.warning("%d match(s) in file %s : %s.", count, src,
                           rule.get('description'))
            findings += count
        content = newcontent

    return (findings, content)


def main():
    """Entry point for this script."""

    parser, args = parse_command_line_arguments()
    logger = initialize_logging(args.debug, args.less_verbose)

    result = 0

    if args.download:
        try:
            download_listing(args.listing)
        except DownloadRetfListingFailed as ex:
            logger.error("Downloading latest RETF listing failed: %s.", ex)
            result = 1

    if not args.path and not args.file and not args.download:
        parser.print_help()
        result = 2

    if not result and not os.path.isfile(args.listing):
        logger.error("RETF listing not found at %s.", args.listing)
        logger.info("Please download the RETF listing first by using the "
                    "parameter --download.")
        result = 1

    if not result:
        files = get_file_listing(args.path, args.file, args.extension)

        rules = generate_listing(args.listing)
        disabled = load_disabled_rules(args.disabled)

        all_findings = 0
        for check in files:
            if not os.path.isfile(check):
                continue

            (findings, content) = check_file(check, rules, disabled)

            if findings > 0:
                all_findings += findings
                logger.warning("%s finding(s) in file %s.", findings, check)

            if findings > 0 and args.write_changes:
                write_text_to_file(check, content, args.no_backup,
                                   args.in_place)

        if all_findings > 0:
            logger.warning("%s finding(s) in all checked files.", all_findings)
            result = 1

    return result

if __name__ == "__main__":
    sys.exit(main())
