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

'''
Usage:
    test.py [path]

Validates all xml files against the DocBook 5 RELAX NG schema, and
attempts to build all books.

Options:
    path     Root directory, defaults to <repo root>/doc

Ignores pom.xml files and subdirectories named "target".

Requires:
    - Python 2.7 or greater
    - lxml Python library
    - Maven
'''

import gzip
import json
import multiprocessing
import operator
import os
import re
import shutil
import subprocess
import sys
import time
import urllib2

from lxml import etree
from oslo.config import cfg

import os_doc_tools
from os_doc_tools.common import check_output   # noqa
from os_doc_tools.openstack.common import log


LOG = log.getLogger('openstack-doc-test')

# These are files that are known to not pass syntax or niceness checks
# Add values via --file-exceptions.
FILE_EXCEPTIONS = []

# These are files that are known to not be in DocBook XML format.
# Add values via --build-file-exceptions.
BUILD_FILE_EXCEPTIONS = []

# These are books that we aren't checking yet.
BOOK_EXCEPTIONS = []

# Mappings from books to build directories under target
BOOK_MAPPINGS = {}

# Mappings from books to publish directories
BOOK_PUBLISH_MAPPINGS = {}

RESULTS_OF_BUILDS = []

# List of recognized (allowable) os profiling directives.
KNOWN_OS_VALUES = ["debian",
                   "centos",
                   "fedora",
                   "opensuse",
                   "rhel",
                   "sles",
                   "ubuntu"]


# List of recognized (allowable) audience profiling directives.
KNOWN_AUDIENCE_VALUES = ["enduser",
                         "adminuser",
                         "installer",
                         "webpage"]

OS_DOC_TOOLS_DIR = os.path.dirname(__file__)
# NOTE(jaegerandi): BASE_RNG needs to end with '/', otherwise
# the etree.parse call in get_wadl_schema will fail.
BASE_RNG = os.path.join(OS_DOC_TOOLS_DIR, 'resources/')
RACKBOOK_RNG = os.path.join(BASE_RNG, 'rackbook.rng')
DOCBOOKXI_RNG = os.path.join(BASE_RNG, 'docbookxi.rng')
WADL_RNG = os.path.join(BASE_RNG, 'wadl.rng')
WADL_XSD = os.path.join(BASE_RNG, 'wadl.xsd')

SCRIPTS_DIR = os.path.join(OS_DOC_TOOLS_DIR, 'scripts')


def get_schema(is_api_site=False):
    """Return the DocBook RELAX NG schema."""
    if is_api_site:
        url = RACKBOOK_RNG
    else:
        url = DOCBOOKXI_RNG
    relaxng_doc = etree.parse(url)
    return etree.RelaxNG(relaxng_doc)


def get_wadl_schema():
    """Return the Wadl schema."""
    # NOTE(jaegerandi): We could use the RelaxNG instead
    # like follows but this gives quite some errors at the
    # moment, so only validate using the XMLSchema
    # url = WADL_RNG
    # relaxng_doc = etree.parse(url, base_url=BASE_RNG)
    # return etree.RelaxNG(relaxng_doc)
    url = WADL_XSD
    schema = etree.parse(url, base_url=BASE_RNG)
    return etree.XMLSchema(schema)


def validation_failed(schema, doc):
    """Return True if the parsed doc fails against the schema.

    This will ignore validation failures of the type: IDREF attribute linkend
    references an unknown ID. This is because we are validating individual
    files that are being imported, and sometimes the reference isn't present
    in the current file.
    """
    return (not schema.validate(doc) and
            any(log.type_name != "DTD_UNKNOWN_ID" for log in schema.error_log))


def verify_section_tags_have_xmlid(doc):
    """Check that all section tags have an xml:id attribute.

    Will throw an exception if there's at least one missing.
    """
    ns = {"docbook": "http://docbook.org/ns/docbook"}
    for node in doc.xpath('//docbook:section', namespaces=ns):
        if "{http://www.w3.org/XML/1998/namespace}id" not in node.attrib:
            raise ValueError("section missing xml:id attribute, line %d" %
                             node.sourceline)


def verify_attribute_profiling(doc, attribute, known_values):
    """Check for conflicts in attribute profiling.

    Check for elements with attribute profiling set that conflicts with
    the attribute profiling of nodes below them in the DOM
    tree. This picks up cases where content is accidentally
    omitted via conflicting profiling. Checks known_values also for
    supported profiling values.
    """

    msg = []
    ns = {"docbook": "http://docbook.org/ns/docbook"}
    path = '//docbook:*[@%s]' % attribute
    for parent in doc.xpath(path, namespaces=ns):
        p_tag = parent.tag
        p_line = parent.sourceline
        p_att_list = parent.attrib[attribute].split(';')

        for att in p_att_list:
            if att not in known_values:
                msg.append(
                    "'%s' is not a recognized %s profile on line %d." %
                    (att, attribute, p_line))

        cpath = './/docbook:*[@%s]' % attribute
        for child in parent.xpath(cpath, namespaces=ns):
            c_tag = child.tag
            c_line = child.sourceline
            c_att_list = child.attrib[attribute].split(';')
            for att in c_att_list:
                if att not in p_att_list:
                    len_ns = len("{http://docbook.org/ns/docbook}")
                    msg.append(
                        "%s %s profiling (%s) conflicts with %s "
                        "profiling of %s on line %d." %
                        (p_tag[len_ns:], attribute, p_att_list,
                         attribute, c_tag[len_ns:], c_line))
    if len(msg) > 0:
        raise ValueError("\n     ".join(msg))


def verify_profiling(doc):
    """"Check profiling information."""
    verify_attribute_profiling(doc, "os", KNOWN_OS_VALUES)
    verify_attribute_profiling(doc, "audience", KNOWN_AUDIENCE_VALUES)


def verify_whitespace_niceness(docfile):
    """Check that no unnecessary whitespaces are used."""
    checks = [
        re.compile(".*\s+\n$"),
    ]

    elements = [
        'listitem',
        'para',
        'td',
        'th',
        'command',
        'literal',
        'title',
        'caption',
        'filename',
        'userinput',
        'programlisting'
    ]

    for element in elements:
        checks.append(re.compile(".*<%s>\s+[\w\-().:!?{}\[\]]+.*\n"
                                 % element))
        checks.append(re.compile(".*[\w\-().:!?{}\[\]]+\s+<\/%s>.*\n"
                                 % element))

    lc = 0
    affected_lines = []
    tab_lines = []
    nbsp_lines = []
    for line in open(docfile, 'r'):
        lc = lc + 1
        if '\t' in line:
            tab_lines.append(str(lc))

        if '\xc2\xa0' in line:
            nbsp_lines.append(str(lc))
        for check in checks:
            if check.match(line) and lc not in affected_lines:
                affected_lines.append(str(lc))

    msg = ""
    if nbsp_lines:
        msg = "non-breaking space found in lines (use &nbsp;): %s" % (
            ", ".join(nbsp_lines))
    if affected_lines:
        if (msg):
            msg += "\n    "
        msg += ("trailing or unnecessary whitespaces found in lines: %s"
                % (", ".join(affected_lines)))
    if tab_lines:
        if (msg):
            msg += "\n    "
        msg += "tabs found in lines: %s" % ", ".join(tab_lines)

    if msg:
        raise ValueError(msg)


def verify_valid_links(doc):
    """Check that all linked URLs are reachable

    Will throw an exception if there's at least one unreachable URL.
    """
    ns = {"docbook": "http://docbook.org/ns/docbook",
          'xlink': 'http://www.w3.org/1999/xlink'}
    msg = []
    for node in doc.xpath('//docbook:link', namespaces=ns):
        try:
            url = node.attrib['{http://www.w3.org/1999/xlink}href']
        except Exception:
            continue

        try:
            urllib2.urlopen(url)
        except urllib2.HTTPError as e:
            # Ignore some error codes:
            # 403 (Forbidden) since it often means that the user-agent
            # is wrong.
            # 503 (Service Temporarily Unavailable)
            if e.code not in [403, 503]:
                e_line = node.sourceline
                msg.append("URL %s not reachable at line %d, error %s" % (
                    url, e_line, e))
        except urllib2.URLError as e:
            e_line = node.sourceline
            msg.append("URL %s invalid at line %d, error %s" % (
                url, e_line, e))

    if len(msg) > 0:
        raise ValueError("\n    ".join(msg))


def error_message(error_log):
    """Return a string that contains the error message.

    We use this to filter out false positives related to IDREF attributes
    """
    errs = [str(x) for x in error_log if x.type_name != 'DTD_UNKNOWN_ID']

    # Reverse output so that earliest failures are reported first
    errs.reverse()
    return "\n".join(errs)


def www_touched():
    """Check whether files in www directory are touched."""

    try:
        git_args = ["git", "diff", "--name-only", "HEAD~1", "HEAD"]
        modified_files = check_output(git_args).strip().split()
    except (subprocess.CalledProcessError, OSError) as e:
        print("git failed: %s" % e)
        sys.exit(1)

    www_changed = False
    other_changed = False
    for f in modified_files:
        if f.startswith("www/"):
            www_changed = True
        else:
            other_changed = True

    return www_changed and not other_changed


def check_modified_affects_all(rootdir):
    """Check whether special files were modified.

    There are some special files where we should rebuild all books
    if either of these is touched.
    """

    os.chdir(rootdir)

    try:
        git_args = ["git", "diff", "--name-only", "HEAD~1", "HEAD"]
        modified_files = check_output(git_args).strip().split()
    except (subprocess.CalledProcessError, OSError) as e:
        print("git failed: %s" % e)
        sys.exit(1)

    special_files = [
        # Top-Level pom.xml
        "pom.xml",
        # doc/pom.xml in openstack-manuals
        "doc/pom.xml"
    ]

    for f in modified_files:
        if f in special_files or f.endswith('.ent'):
            if cfg.CONF.verbose:
                print("File %s modified, this affects all books." % f)
            return True

    return False


def get_modified_files(rootdir, filtering=None):
    """Get modified files below doc directory."""

    # There are several tree traversals in this program that do a
    # chdir, we need to run this git command always from the rootdir,
    # so assure that.
    os.chdir(rootdir)

    try:
        git_args = ["git", "diff", "--name-only", "--relative", "HEAD~1",
                    "HEAD"]
        if filtering is not None:
            git_args.append(filtering)
        modified_files = check_output(git_args).strip().split()
    except (subprocess.CalledProcessError, OSError) as e:
        print("git failed: %s" % e)
        sys.exit(1)
    return modified_files


def filter_dirs(dirs):
    """Return list of directories to descend into."""

    # Don't descend into 'locale', 'target', and 'publish-docs'
    # subdirectories and filter out any dot directories

    return [d for d in dirs if (d != 'target' and
                                d != 'publish-docs' and
                                d != 'locale' and
                                not d.startswith('.'))]


def check_deleted_files(rootdir, file_exceptions, verbose):
    """Checking that no removed files are referenced."""

    print("Checking that no removed files are referenced...")
    deleted_files = get_modified_files(rootdir, "--diff-filter=D")
    if not deleted_files:
        print("No files were removed.\n")
        return 0

    if verbose:
        print(" Removed files:")
        for f in deleted_files:
            print ("   %s" % f)

    deleted_files = [os.path.abspath(x) for x in deleted_files]
    no_checked_files = 0

    # Figure out whether files were included anywhere
    missing_reference = False

    for root, dirs, files in os.walk(rootdir):
        dirs[:] = filter_dirs(dirs)

        os.chdir(root)

        for f in files:
            if not is_testable_xml_file(f, file_exceptions):
                continue

            path = os.path.abspath(os.path.join(root, f))
            try:
                doc = etree.parse(path)
            except etree.XMLSyntaxError as e:
                print(" Warning: file %s is invalid XML: %s" % (path, e))
                continue

            no_checked_files = no_checked_files + 1

            # Check for inclusion of files as part of imagedata
            for node in doc.findall(
                    '//{http://docbook.org/ns/docbook}imagedata'):
                href = node.get('fileref')
                if (f not in file_exceptions and
                        os.path.abspath(href) in deleted_files):
                    print("  File %s has imagedata href for deleted "
                          "file %s" % (f, href))
                    missing_reference = True

                    break

            # Check for inclusion of files as part of xi:include
            ns = {"xi": "http://www.w3.org/2001/XInclude"}
            for node in doc.xpath('//xi:include', namespaces=ns):
                href = node.get('href')
                if (os.path.abspath(href) in deleted_files):
                    print("  File %s has an xi:include on deleted file %s"
                          % (f, href))
                    missing_reference = True

    if missing_reference:
        print("Check failed, %d files were removed, "
              "%d files checked.\n"
              % (len(deleted_files), no_checked_files))
        return 1

    print("Check passed, %d files were removed, "
          "%d files checked.\n"
          % (len(deleted_files), no_checked_files))
    return 0


def validate_one_json_file(rootdir, path, verbose, check_syntax,
                           check_niceness):
    """Validate a single JSON file."""

    any_failures = False
    if verbose:
        print(" Validating %s" % os.path.relpath(path, rootdir))

    try:
        if check_syntax:
            json_file = open(path, 'rb')
            json.load(json_file)
    except ValueError as e:
        any_failures = True
        print("  Invalid JSON file %s: %s" %
              (os.path.relpath(path, rootdir), e))
    try:
        if check_niceness:
            verify_whitespace_niceness(path)
    except ValueError as e:
        any_failures = True
        print("  %s: %s" % (os.path.relpath(path, rootdir), e))

    return any_failures


def validate_one_file(schema, rootdir, path, verbose,
                      check_syntax, check_niceness, check_links,
                      validate_schema):
    """Validate a single file."""
    # We pass schema in as a way of caching it, generating it is expensive

    any_failures = False
    if verbose:
        print(" Validating %s" % os.path.relpath(path, rootdir))
    try:
        if check_syntax or check_links:
            doc = etree.parse(path)
            if check_syntax:
                if validate_schema:
                    if validation_failed(schema, doc):
                        any_failures = True
                        print(error_message(schema.error_log))
                    verify_section_tags_have_xmlid(doc)
                    verify_profiling(doc)
            if check_links:
                    verify_valid_links(doc)
        if check_niceness:
            verify_whitespace_niceness(path)
    except etree.XMLSyntaxError as e:
        any_failures = True
        print("  %s: %s" % (os.path.relpath(path, rootdir), e))
    except ValueError as e:
        any_failures = True
        print("  %s: %s" % (os.path.relpath(path, rootdir), e))

    return any_failures


def is_testable_xml_file(path, exceptions):
    """Returns true if file ends with .xml and is not a pom.xml file."""

    filename = os.path.basename(path)
    return (filename.endswith('.xml') and not filename == 'pom.xml' and
            filename not in exceptions)


def is_testable_file(path, exceptions):
    """Returns true if file is in some XML format we handle

    Skips pom.xml files as well since those are not handled.
    """

    filename = os.path.basename(path)
    return (filename.endswith(('.xml', '.xsd', '.xsl', '.wadl',
                               '.xjb', '.json')) and
            not filename == 'pom.xml' and filename not in exceptions)


def is_wadl(filename):
    """Returns true if file ends with .wadl."""

    return filename.endswith('.wadl')


def is_json(filename):
    """Returns true if file ends with .json."""

    return filename.endswith('.json')


def validate_individual_files(files_to_check, rootdir, verbose,
                              check_syntax=False, check_niceness=False,
                              check_links=False, is_api_site=False):
    """Validate list of files."""

    schema = get_schema(is_api_site)
    if is_api_site:
        wadl_schema = get_wadl_schema()

    any_failures = False
    no_validated = 0
    no_failed = 0

    checks = []
    if check_links:
        checks.append("valid URL links")
    if check_niceness:
        checks.append("niceness")
    if check_syntax:
        checks.append("syntax")
    print("Checking XML files for %s..." % (", ".join(checks)))

    for f in files_to_check:
        validate_schema = True
        if is_api_site:
            # Files ending with ".xml" in subdirectories of
            # wadls and samples files are not docbook files.
            if (f.endswith('.xml') and
               ("wadls" in f or "samples" in f)):
                validate_schema = False
            # Right now we can only validate docbook .xml
            # and .wadl files with a schema
            elif not f.endswith(('.wadl', '.xml')):
                validate_schema = False

        if is_json(f):
            any_failures = validate_one_json_file(rootdir, f,
                                                  verbose,
                                                  check_syntax,
                                                  check_niceness)
        elif (is_api_site and is_wadl(f)):
            any_failures = validate_one_file(wadl_schema, rootdir, f,
                                             verbose,
                                             check_syntax,
                                             check_niceness,
                                             check_links,
                                             validate_schema)
        else:
            any_failures = validate_one_file(schema, rootdir, f,
                                             verbose,
                                             check_syntax,
                                             check_niceness,
                                             check_links,
                                             validate_schema)
        if any_failures:
            no_failed = no_failed + 1
        no_validated = no_validated + 1

    if no_failed > 0:
        print("Check failed, validated %d XML files with %d failures.\n"
              % (no_validated, no_failed))
        return 1
    else:
        print("Check passed, validated %d XML files.\n" % no_validated)
    return 0


def validate_modified_files(rootdir, exceptions, verbose,
                            check_syntax=False, check_niceness=False,
                            check_links=False, is_api_site=False):
    """Validate list of modified files."""

    # Do not select deleted files, just Added, Copied, Modified, Renamed,
    # or Type changed
    modified_files = get_modified_files(rootdir, "--diff-filter=ACMRT")
    modified_files = [f for f in modified_files if
                      is_testable_file(f, exceptions)]

    return validate_individual_files(modified_files, rootdir,
                                     verbose,
                                     check_syntax, check_niceness,
                                     check_links, is_api_site)


def validate_all_files(rootdir, exceptions, verbose,
                       check_syntax, check_niceness=False,
                       check_links=False, is_api_site=False):
    """Validate all xml files."""

    files_to_check = []

    for root, dirs, files in os.walk(rootdir):
        dirs[:] = filter_dirs(dirs)

        for f in files:
            # Ignore maven files, which are called pom.xml
            if is_testable_file(f, exceptions):
                path = os.path.abspath(os.path.join(root, f))
                files_to_check.append(path)

    return validate_individual_files(files_to_check, rootdir,
                                     verbose,
                                     check_syntax, check_niceness,
                                     check_links, is_api_site)


def logging_build_book(result):
    """Callback for book building."""
    RESULTS_OF_BUILDS.append(result)


def get_gitroot():
    """Return path to top-level of git repository."""

    try:
        git_args = ["git", "rev-parse", "--show-toplevel"]
        gitroot = check_output(git_args).rstrip()
    except (subprocess.CalledProcessError, OSError) as e:
        print("git failed: %s" % e)
        sys.exit(1)

    return gitroot


def print_gitinfo():
    """Print information about repository and change."""

    try:
        git_cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        gitbranch = check_output(git_cmd).rstrip()
        git_cmd = ["git", "show", "--format=%s", "-s"]
        gitsubject = check_output(git_cmd).rstrip()
        git_cmd = ["git", "show", "--format=%an", "-s"]
        gitauthor = check_output(git_cmd).rstrip()
    except (subprocess.CalledProcessError, OSError) as e:
        print("git failed: %s" % e)
        sys.exit(1)
    print("Testing patch:")
    print("  Title: %s" % gitsubject)
    print("  Author: %s" % gitauthor)
    print("  Branch: %s" % gitbranch)


def get_publish_path():
    """Return path to use of publishing books."""

    return os.path.join(get_gitroot(), 'publish-docs')


def ignore_for_publishing(_, names):
    """Return list of files that should be ignored for publishing."""

    # Ignore:
    # - all files ending with .xml with the exception of atom.xml
    # - all files ending with .fo
    # The directory named wadls

    f = [n for n in names if ((n.endswith('.xml') and n != 'atom.xml')
                              or (n.endswith('.fo') or n == 'wadls'))]
    return f


def publish_book(publish_path, book):
    """Copy generated files to publish_path."""

    # Assumption: The path for the book is the same as the name of directory
    # the book is in. We need to special case any exceptions.

    # Publishing directory
    book_path = publish_path

    if cfg.CONF.language:
        book_path = os.path.join(book_path, cfg.CONF.language)

    if os.path.isdir(os.path.join('target/docbkx/webhelp', book)):
        source = os.path.join('target/docbkx/webhelp', book)
    elif os.path.isdir(os.path.join('target/docbkx/webhelp/local', book)):
        source = os.path.join('target/docbkx/webhelp/local', book)
        book_path = os.path.join(book_path, 'local')
    elif os.path.isdir(os.path.join('target/docbkx/webhelp/',
                                    cfg.CONF.release_path, book)):
        source = os.path.join('target/docbkx/webhelp/',
                              cfg.CONF.release_path, book)
        book_path = os.path.join(book_path, cfg.CONF.release_path)
    elif (book in BOOK_MAPPINGS):
        source = BOOK_MAPPINGS[book]
    else:
        if cfg.CONF.debug:
            print("No build result found for book %s" % book)
        return

    if book in BOOK_PUBLISH_MAPPINGS:
        book_publish_dir = BOOK_PUBLISH_MAPPINGS[book]
    else:
        book_publish_dir = book

    book_path = os.path.join(book_path, book_publish_dir)
    if cfg.CONF.debug:
        print("Uploading book %s to %s" % (book, book_path))

    # Note that shutil.copytree does not allow an existing target directory,
    # thus delete it.
    shutil.rmtree(book_path, ignore_errors=True)

    shutil.copytree(source, book_path,
                    ignore=ignore_for_publishing)


def ensure_exists(program):
    """Check that program exists, abort if not."""
    retcode = subprocess.call(['which', program], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    if retcode != 0:
        print("Program '%s' does not exist, please install!" % program)
        sys.exit(1)


def build_book(book, publish_path, log_path):
    """Build book(s) in directory book."""

    # Note that we cannot build in parallel several books in the same
    # directory like the Install Guide. Thus we build sequentially per
    # directory.
    os.chdir(book)
    result = True
    returncode = 0
    if cfg.CONF.debug:
        print("Building in directory '%s'" % book)
    base_book = os.path.basename(book)
    base_book_orig = base_book
    comments = "-Dcomments.enabled=%s" % cfg.CONF.comments_enabled
    release = "-Drelease.path.name=%s" % cfg.CONF.release_path
    if cfg.CONF.language:
        out_filename = ("build-" + cfg.CONF.language + "-" + base_book +
                        ".log.gz")
    else:
        out_filename = "build-" + base_book + ".log.gz"
    out_file = gzip.open(os.path.join(log_path, out_filename), 'w')
    output = ""
    try:
        # Clean first and then build so that the output of all guides
        # is available
        output = subprocess.check_output(
            ["mvn", "clean"],
            stderr=subprocess.STDOUT
        )
        out_file.write(output)
        if base_book == "install-guide":
            # Build Debian
            base_book = "install-guide (for debian)"
            output = subprocess.check_output(
                ["mvn", "generate-sources", "-B",
                 comments, release,
                 "-Doperating.system=apt-debian", "-Dprofile.os=debian"],
                stderr=subprocess.STDOUT
            )
            out_file.write(output)
            # Build Fedora
            base_book = "install-guide (for Fedora)"
            output = subprocess.check_output(
                ["mvn", "generate-sources", "-B",
                 comments, release,
                 "-Doperating.system=yum",
                 "-Dprofile.os=centos;fedora;rhel"],
                stderr=subprocess.STDOUT
            )
            out_file.write(output)
            # Build openSUSE
            base_book = "install-guide (for openSUSE)"
            output = subprocess.check_output(
                ["mvn", "generate-sources", "-B",
                 comments, release,
                 "-Doperating.system=zypper", "-Dprofile.os=opensuse;sles"],
                stderr=subprocess.STDOUT
            )
            out_file.write(output)
            # Build Ubuntu
            base_book = "install-guide (for Ubuntu)"
            output = subprocess.check_output(
                ["mvn", "generate-sources", "-B",
                 comments, release,
                 "-Doperating.system=apt", "-Dprofile.os=ubuntu"],
                stderr=subprocess.STDOUT
            )
            # Success
            base_book = "install-guide (for Debian, Fedora, openSUSE, Ubuntu)"
        # HOT template guide
        elif base_book == 'hot-guide':
            # Make sure that the build dir is clean
            if os.path.isdir('build'):
                shutil.rmtree('build')
            # Generate the DN XML
            output = subprocess.check_output(
                ["make", "xml"],
                stderr=subprocess.STDOUT
            )
            out_file.write(output)
            # Generate the docbook book
            output = subprocess.check_output(
                ["openstack-dn2osdbk", "build/xml", "build/docbook",
                 "--toplevel", "book"],
                stderr=subprocess.STDOUT
            )
            out_file.write(output)
            output = subprocess.check_output(
                ["mvn", "generate-sources", comments, release, "-B"],
                stderr=subprocess.STDOUT
            )
        # Repository: identity-api
        elif (cfg.CONF.repo_name == "identity-api"
              and book.endswith("v3")):
            output = subprocess.check_output(
                ["bash", os.path.join(SCRIPTS_DIR, "markdown-docbook.sh"),
                 "identity-api-v3"],
                stderr=subprocess.STDOUT
            )
            out_file.write(output)
            # File gets generated at wrong directory, we need to move it
            # around
            if os.path.isfile('identity-api-v3.xml'):
                os.remove('identity-api-v3.xml')
            shutil.move("src/markdown/identity-api-v3.xml", ".")
            output = subprocess.check_output(
                ["mvn", "generate-sources", comments, release, "-B"],
                stderr=subprocess.STDOUT
            )
        # Repository: image-api
        elif base_book == 'image-api-v2':
            output = subprocess.check_output(
                ["bash", os.path.join(SCRIPTS_DIR, "markdown-docbook.sh"),
                 "image-api-v2.0"],
                stderr=subprocess.STDOUT
            )
            out_file.write(output)
            output = subprocess.check_output(
                ["mvn", "generate-sources", comments, release, "-B"],
                stderr=subprocess.STDOUT
            )
        else:
            output = subprocess.check_output(
                ["mvn", "generate-sources", comments, release, "-B"],
                stderr=subprocess.STDOUT
            )
    except (subprocess.CalledProcessError, KeyboardInterrupt) as e:
        output = e.output
        returncode = e.returncode
        result = False

    out_file.write(output)
    out_file.close()
    if result:
        publish_book(publish_path, base_book_orig)
    return (base_book, result, output, returncode)


def is_book_master(filename):
    """Check if a file is a book master file.

    Returns True if filename is one of the special filenames used for the
    book master files.

    We do not parse pom.xml for the includes directive to determine
    the top-level files and thus have to use a heuristic.

    """

    return ((filename.startswith(('bk-', 'bk_', 'st-', 'api-'))
             and filename.endswith('.xml')) or
            filename == 'openstack-glossary.xml')


def find_affected_books(rootdir, book_exceptions, file_exceptions,
                        force, ignore_dirs):
    """Check which books are affected by modified files.

    Returns a set with books.
    """
    book_root = rootdir

    books = []
    affected_books = set()

    build_all_books = (force or check_modified_affects_all(rootdir) or
                       cfg.CONF.only_book)

    # Dictionary that contains a set of files.
    # The key is a filename, the set contains files that include this file.
    included_by = {}

    # Dictionary with books and their bk*.xml files
    book_bk = {}

    # List of absolute paths of ignored directories
    abs_ignore_dirs = []
    # 1. Iterate over whole tree and analyze include files.
    # This updates included_by, book_bk and books.
    for root, dirs, files in os.walk(rootdir):
        dirs[:] = filter_dirs(dirs)

        # Filter out directories to be ignored
        if ignore_dirs:
            for d in dirs:
                if d in ignore_dirs:
                    abs_ignore_dirs.append(
                        os.path.join(os.path.join(root, d)))
            dirs[:] = [d for d in dirs if d not in ignore_dirs]

        if os.path.basename(root) in book_exceptions:
            break
        # Do not process files in doc itself or top-level directory
        elif root.endswith('doc') or root == rootdir:
            continue
        elif ("pom.xml" in files and (not cfg.CONF.only_book or
                                      os.path.basename(root) in
                                      cfg.CONF.only_book)):
                books.append(root)
                book_root = root

        # No need to check single books if we build all, we just
        # collect list of books
        if build_all_books:
            continue

        for f in files:
            f_base = os.path.basename(f)
            f_abs = os.path.abspath(os.path.join(root, f))
            if is_book_master(f_base):
                book_bk[f_abs] = book_root
            if not is_testable_xml_file(f, file_exceptions):
                continue

            try:
                doc = etree.parse(f_abs)
            except etree.XMLSyntaxError as e:
                print("  Warning: file %s is invalid XML: %s" % (f_abs, e))
                continue
            for node in doc.findall(
                    '//{http://docbook.org/ns/docbook}imagedata'):
                href = node.get('fileref')
                href_abs = os.path.abspath(os.path.join(root, href))
                if href_abs in included_by:
                    included_by[href_abs].add(f_abs)
                else:
                    included_by[href_abs] = set([f_abs])

            ns = {"xi": "http://www.w3.org/2001/XInclude"}
            for node in doc.xpath('//xi:include', namespaces=ns):
                href = node.get('href')
                href_abs = os.path.abspath(os.path.join(root, href))
                if href_abs in included_by:
                    included_by[href_abs].add(f_abs)
                else:
                    included_by[href_abs] = set([f_abs])

            ns = {"wadl": "http://wadl.dev.java.net/2009/02"}
            for node in doc.xpath('//wadl:resource', namespaces=ns):
                href = node.get('href')
                hash_sign = href.rfind('#')
                if hash_sign != -1:
                    href = href[:hash_sign]
                href_abs = os.path.abspath(os.path.join(root, href))
                if href_abs in included_by:
                    included_by[href_abs].add(f_abs)
                else:
                    included_by[href_abs] = set([f_abs])
            for node in doc.xpath('//wadl:resources', namespaces=ns):
                href = node.get('href')
                # wadl:resources either have a href directly or a child
                # wadl:resource that has a href. So, check that we have
                # a href.
                if href:
                    hash_sign = href.rfind('#')
                    if hash_sign != -1:
                        href = href[:hash_sign]
                    href_abs = os.path.abspath(os.path.join(root, href))
                    if href_abs in included_by:
                        included_by[href_abs].add(f_abs)
                    else:
                        included_by[href_abs] = set([f_abs])

    # Print list of files that are not included anywhere
    if cfg.CONF.print_unused_files:
        print("Checking for files that are not included anywhere...")
        print(" Note: This only looks at files included by an .xml file "
              "but not for files included by other files like .wadl.")
        for root, dirs, files in os.walk(rootdir):
            dirs[:] = filter_dirs(dirs)

            # Filter out directories to be ignored
            if ignore_dirs:
                dirs[:] = [d for d in dirs if d not in ignore_dirs]

            for f in files:
                f_base = os.path.basename(f)
                f_abs = os.path.abspath(os.path.join(root, f))

                if (f_abs not in included_by and f_base != "pom.xml"
                   and not is_book_master(f_base)):
                    f_rel = os.path.relpath(f_abs, rootdir)
                    print ("  %s " % f_rel)
        print("\n")

    if not build_all_books:
        # Generate list of modified_files
        # Do not select deleted files, just Added, Copied, Modified, Renamed,
        # or Type changed
        modified_files = get_modified_files(rootdir, "--diff-filter=ACMRT")
        modified_files = [os.path.abspath(f) for f in modified_files]
        if ignore_dirs:
            for idir in abs_ignore_dirs:
                non_ignored_files = []
                for f in modified_files:
                    if not f.startswith(idir):
                        non_ignored_files.append(f)
                modified_files = non_ignored_files

        # 2. Find all modified files and where they are included

        # List of files that we have to iterate over, these are affected
        # by some modification
        new_files = modified_files

        # All files that are affected (either directly or indirectly)
        affected_files = set(modified_files)

        # 3. Iterate over files that have includes on modified files
        # and build a closure - the set of all files (affected_files)
        # that have a path to a modified file via includes.
        while len(new_files) > 0:
            new_files_to_check = new_files
            new_files = []
            for f in new_files_to_check:
                if "doc/hot-guide/" in f:
                    affected_books.add('hot-guide')
                    continue
                # Skip bk*.xml files
                if is_book_master(os.path.basename(f)):
                    book_modified = book_bk[f]
                    if book_modified not in affected_books:
                        affected_books.add(book_modified)
                    continue
                if f not in included_by:
                    continue
                for g in included_by[f]:
                    if g not in affected_files:
                        new_files.append(g)
                        affected_files.add(g)

    if cfg.CONF.only_book:
        print("Building specified books.")
    elif build_all_books:
        print("Building all books.")
    elif affected_books:
        books = affected_books
    else:
        print("No books are affected by modified files. Building all books.")

    return books


def generate_index_file():
    """Generate index.html file in publish_path."""

    publish_path = get_publish_path()
    if not os.path.isdir(publish_path):
        os.mkdir(publish_path)

    index_file = open(os.path.join(get_publish_path(), 'index.html'), 'w')

    index_file.write(
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n'
        '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        '<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">\n'
        '<body>\n'
        '<h1>Results of checkbuild</h1>\n')

    for root, dirs, files in os.walk(publish_path):

        dirs[:] = [d for d in dirs if d not in ['common', 'webapp', 'content']]

        # Ignore top-level index.html files
        if root == publish_path:
            continue

        if os.path.isfile(os.path.join(root, 'content/index.html')):
            path = os.path.relpath(root, publish_path)
            index_file.write('<a href="%s/content/index.html">%s</a>\n' %
                             (path, path))
            index_file.write('<br/>\n')

        if os.path.isfile(os.path.join(root, 'api-ref.html')):
            path = os.path.relpath(root, publish_path)
            index_file.write('<a href="%s/api-ref.html">%s</a>\n' %
                             (path, path))
            index_file.write('<br/>\n')

        # List PDF files for api-site that have from "bk-api-ref*.pdf"
        # as well since they have no corresponding html file.
        for f in files:
            if f.startswith('bk-api-ref') and f.endswith('.pdf'):
                path = os.path.relpath(root, publish_path)
                index_file.write('<a href="%s/%s">%s</a>\n' %
                                 (path, f, f))
                index_file.write('<br/>\n')

    if os.path.isfile(os.path.join(get_publish_path(), 'www-index.html')):
        index_file.write('<br/>\n')
        index_file.write('<a href="www-index.html">list of generated '
                         'WWW pages</a>\n')
    index_file.write('</body>\n'
                     '</html>\n')
    index_file.close()


def build_affected_books(rootdir, book_exceptions, file_exceptions,
                         force=False, ignore_dirs=None):
    """Build all the books which are affected by modified files.

    Looks for all directories with "pom.xml" and checks if a
    XML file in the directory includes a modified file. If at least
    one XML file includes a modified file the method calls
    "mvn clean generate-sources" in that directory.

    This will throw an exception if a book fails to build
    """

    if ignore_dirs is None:
        ignore_dirs = []

    books = find_affected_books(rootdir, book_exceptions,
                                file_exceptions, force, ignore_dirs)

    # Remove cache content which can cause build failures
    shutil.rmtree(os.path.expanduser("~/.fop"),
                  ignore_errors=True)

    maxjobs = multiprocessing.cpu_count()
    # Jenkins fails sometimes with errors if too many jobs run, artificially
    # limit to 4 for now.
    # See https://bugs.launchpad.net/openstack-manuals/+bug/1221721
    if maxjobs > 4:
        maxjobs = 4
    pool = multiprocessing.Pool(maxjobs)
    print("Queuing the following books for building:")
    publish_path = get_publish_path()
    log_path = get_gitroot()
    first_book = True

    # First show books
    for book in sorted(books):
        print("  %s" % os.path.basename(book))
    print("Building all queued %d books now..." % len(books))

    # And then queue - since we wait for the first book to finish.
    try:
        for book in sorted(books):
            if cfg.CONF.debug or not cfg.CONF.parallel:
                (book, result, output, retcode) = build_book(book,
                                                             publish_path,
                                                             log_path)
                logging_build_book([book, result, output, retcode])
            else:
                res = pool.apply_async(build_book,
                                       (book, publish_path, log_path),
                                       callback=logging_build_book)
                if first_book:
                    first_book = False
                    # The first invocation of maven might download loads of
                    # data locally, we cannot do this in parallel. So, wait
                    # here for the first job to finish before running further
                    # mvn jobs.
                    res.get()
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        pool.terminate()
        pool.join()

    any_failures = False
    for book, result, _, _ in sorted(RESULTS_OF_BUILDS,
                                     key=operator.itemgetter(0)):
        if result:
            print(">>> Build of book %s succeeded." % book)
        else:
            any_failures = True

    if cfg.CONF.create_index:
        generate_index_file()

    if any_failures:
        for book, result, output, returncode in RESULTS_OF_BUILDS:
            if not result:
                print(">>> Build of book %s failed (returncode = %d)."
                      % (book, returncode))
                print("\n%s" % output)

        print("Building of books finished with failures.\n")
        return 1
    else:
        print("Building of books finished successfully.\n")

    if len(RESULTS_OF_BUILDS) != len(books):
        print("ERROR: %d queued for building but only %d build!" %
              (len(books), len(RESULTS_OF_BUILDS)))
        return 1
    return 0


def add_exceptions(file_exception, verbose):
    """Add list of exceptions from file_exceptions."""

    for entry in file_exception:
        if verbose:
            print(" Adding file to ignore list: %s" % entry)
        FILE_EXCEPTIONS.append(entry)


def add_build_exceptions(build_file_exception, verbose):
    """Add list of exceptions from build_file_exceptions."""

    for entry in build_file_exception:
        if verbose:
            print(" Adding file to build ignore list: %s" % entry)
        BUILD_FILE_EXCEPTIONS.append(entry)


cli_OPTS = [
    cfg.BoolOpt("api-site", default=False,
                help="Enable special handling for api-site repository."),
    cfg.BoolOpt('check-all', default=False,
                help="Run all checks."),
    cfg.BoolOpt('check-build', default=False,
                help="Check building of books using modified files."),
    cfg.BoolOpt("check-deletions", default=False,
                help="Check that deleted files are not used."),
    cfg.BoolOpt("check-links", default=False,
                help="Check that linked URLs are valid and reachable."),
    cfg.BoolOpt("check-niceness", default=False,
                help="Check the niceness of files, for example whitespace."),
    cfg.BoolOpt("check-syntax", default=False,
                help="Check the syntax of modified files."),
    cfg.BoolOpt("create-index", default=True,
                help="When publishing create an index.html file to find books "
                "in an easy way."),
    cfg.BoolOpt('force', default=False,
                help="Force the validation of all files "
                "and build all books."),
    cfg.BoolOpt("parallel", default=True,
                help="Build books in parallel (default)."),
    cfg.BoolOpt("print-unused-files", default=False,
                help="Print list of files that are not included anywhere as "
                "part of check-build."),
    cfg.BoolOpt("publish", default=False,
                help="Setup content in publish-docs directory for "
                "publishing to external website."),
    cfg.MultiStrOpt("build-file-exception",
                    help="File that will be skipped during delete and "
                         "build checks to generate dependencies. This should "
                         "be done for invalid XML files only."),
    cfg.MultiStrOpt("file-exception",
                    help="File that will be skipped during niceness and "
                         "syntax validation."),
    cfg.MultiStrOpt("ignore-dir",
                    help="Directory to ignore for building of manuals. The "
                         "parameter can be passed multiple times to add "
                         "several directories."),
    cfg.StrOpt('language', default=None, short='l',
               help="Build translated manual for language in path "
               "generate/$LANGUAGE ."),
    cfg.MultiStrOpt('only-book', default=None,
                    help="Build each specified manual."),
]

OPTS = [
    # NOTE(jaegerandi): books, target-dirs, publish-dir could be a
    # DictOpt but I could not get this working properly.
    cfg.MultiStrOpt("book", default=None,
                    help="Name of book that needs special mapping. "
                    "This is the name of directory where the pom.xml "
                    "file lives."),
    cfg.MultiStrOpt("target-dir", default=None,
                    help="Directory name in target dir for a book. "
                    "The option must be in the same order as the book "
                    "option."),
    cfg.MultiStrOpt("publish-dir", default=None,
                    help="Directory name where book will be copied to "
                    "in publish-docs directory. This option must be in "
                    "same order as the book option. Either give this option "
                    "for all books or for none. If publish-dir is not "
                    "specified, book is used as publish-dir."),
    cfg.StrOpt("repo-name", default=None,
               help="Name of repository."),
    cfg.StrOpt("release-path", default="trunk",
               help="Value to pass to maven for release.path.name."),
    cfg.StrOpt("comments-enabled", default="0",
               help="Value to pass to maven for comments.enabled."),
]


def handle_options():
    """Setup configuration variables from config file and options."""

    CONF = cfg.CONF
    CONF.register_cli_opts(cli_OPTS)
    CONF.register_opts(OPTS)

    default_config_files = [os.path.join(get_gitroot(), 'doc-test.conf')]
    CONF(sys.argv[1:], project='documentation', prog='openstack-doc-test',
         version=os_doc_tools.__version__,
         default_config_files=default_config_files)

    if CONF.repo_name:
        print ("Testing repository '%s'\n" % CONF.repo_name)

    if CONF.verbose:
        print("Verbose execution")

    if CONF.debug:
        print("Enabling debug code")

    if CONF.language:
        print("Building for language '%s'" % CONF.language)

    if CONF.file_exception:
        add_exceptions(CONF.file_exception, CONF.verbose)

    if CONF.build_file_exception:
        add_build_exceptions(CONF.build_file_exception, CONF.verbose)

    if (not CONF.check_build and not CONF.check_deletions and
       not CONF.check_niceness and not CONF.check_syntax and
       not CONF.check_links):
        CONF.check_all = True

    if CONF.check_all:
        CONF.check_deletions = True
        CONF.check_build = True
        CONF.check_links = True
        CONF.check_niceness = True
        CONF.check_syntax = True

    if CONF.publish:
        CONF.create_index = False

    if CONF.check_build and CONF.book and CONF.target_dir:
        if len(CONF.book) != len(CONF.target_dir):
            print("ERROR: book and target_dir options need to have a 1:1 "
                  "relationship.")
            sys.exit(1)
        if (CONF.publish_dir and
           len(CONF.publish_dir) != len(CONF.target_dir)):
            print("ERROR: publish_dir and target_dir need to have a 1:1 "
                  "relationship if publish_dir is specified.")
            sys.exit(1)
        for i in range(len(CONF.book)):
            BOOK_MAPPINGS[CONF.book[i]] = CONF.target_dir[i]
            if CONF.verbose:
                print(" Target dir for %s is %s" %
                      (CONF.book[i], BOOK_MAPPINGS[CONF.book[i]]))
        if CONF.publish_dir:
            for i in range(len(CONF.book)):
                BOOK_PUBLISH_MAPPINGS[CONF.book[i]] = CONF.publish_dir[i]
                if CONF.verbose:
                    print(" Publish dir for %s is %s" %
                          (CONF.book[i], BOOK_PUBLISH_MAPPINGS[CONF.book[i]]))

    if CONF.check_build:
        if CONF.verbose:
            if cfg.CONF.ignore_dir:
                for d in cfg.CONF.ignore_dir:
                    print(" Ignore directory: %s" % d)
            print(" Release path: %s" % cfg.CONF.release_path)
            print(" Comments enabled: %s" % cfg.CONF.comments_enabled)


def doctest():
    """Central entrypoint, parses arguments and runs tests."""

    start_time = time.time()
    CONF = cfg.CONF
    print ("\nOpenStack Doc Checks (using openstack-doc-tools version %s)\n"
           % os_doc_tools.__version__)
    try:
        handle_options()
    except cfg.Error as e:
        print(e)
        return 1
    print_gitinfo()
    errors = 0

    doc_path = get_gitroot()
    if CONF.language:
        doc_path = os.path.join(doc_path, 'generated', CONF.language)
        if CONF.verbose:
            print("Using %s as root" % doc_path)
    elif not CONF.api_site:
        doc_path = os.path.join(doc_path, 'doc')

    if not CONF.force and www_touched():
        print("Only files in www directory changed, nothing to do.\n")
        return

    if CONF.check_syntax or CONF.check_niceness or CONF.check_links:
        if CONF.force:
            errors += validate_all_files(doc_path, FILE_EXCEPTIONS,
                                         CONF.verbose,
                                         CONF.check_syntax,
                                         CONF.check_niceness,
                                         CONF.check_links,
                                         CONF.api_site)
        else:
            errors += validate_modified_files(doc_path, FILE_EXCEPTIONS,
                                              CONF.verbose,
                                              CONF.check_syntax,
                                              CONF.check_niceness,
                                              CONF.check_links,
                                              CONF.api_site)

    if CONF.check_deletions:
        errors += check_deleted_files(doc_path, BUILD_FILE_EXCEPTIONS,
                                      CONF.verbose)

    if CONF.check_build:
        # Some programs are called in subprocesses,  make sure that they
        # really exist.
        ensure_exists("mvn")
        errors += build_affected_books(doc_path, BOOK_EXCEPTIONS,
                                       BUILD_FILE_EXCEPTIONS,
                                       CONF.force,
                                       CONF.ignore_dir)

    elapsed_time = (time.time() - start_time)
    print ("Run time was: %.2f seconds." % elapsed_time)
    if errors == 0:
        print("Congratulations, all tests passed!")
        return 0
    else:
        print("Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(doctest())
