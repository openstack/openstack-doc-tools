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
    - Python 2.7 or greater (for argparse)
    - lxml Python library
    - Maven

'''

import argparse
import multiprocessing
import os
import re
import shutil
import subprocess
import sys

from lxml import etree

import os_doc_tools


# These are files that are known to not be in DocBook format
FILE_EXCEPTIONS = ['st-training-guides.xml',
                   'ha-guide-docinfo.xml']

# These are books that we aren't checking yet
BOOK_EXCEPTIONS = []

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

BASE_RNG = os.path.join(os.path.dirname(__file__), 'resources/')
RACKBOOK_RNG = os.path.join(BASE_RNG, 'rackbook.rng')
DOCBOOKXI_RNG = os.path.join(BASE_RNG, 'docbookxi.rng')
WADL_RNG = os.path.join(BASE_RNG, 'wadl.rng')
WADL_XSD = os.path.join(BASE_RNG, 'wadl.xsd')


# NOTE(berendt): check_output as provided in Python 2.7.5 to make script
#                usable with Python < 2.7
def check_output(*popenargs, **kwargs):
    """Run command with arguments and return its output as a byte string.

    If the exit code was non-zero it raises a CalledProcessError.  The
    CalledProcessError object will have the return code in the returncode
    attribute and output in the output attribute.
    """
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd, output=output)
    return output


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
    #url = WADL_RNG
    #relaxng_doc = etree.parse(url, base_url=BASE_RNG)
    #return etree.RelaxNG(relaxng_doc)
    url = WADL_XSD
    schema = etree.parse(url, base_url=BASE_RNG)
    return etree.XMLSchema(schema)


def validation_failed(schema, doc):
    """Return True if the parsed doc fails against the schema

    This will ignore validation failures of the type: IDREF attribute linkend
    references an unknown ID. This is because we are validating individual
    files that are being imported, and sometimes the reference isn't present
    in the current file.
    """
    return not schema.validate(doc) and \
        any(log.type_name != "DTD_UNKNOWN_ID" for log in schema.error_log)


def verify_section_tags_have_xmid(doc):
    """Check that all section tags have an xml:id attribute

    Will throw an exception if there's at least one missing.
    """
    ns = {"docbook": "http://docbook.org/ns/docbook"}
    for node in doc.xpath('//docbook:section', namespaces=ns):
        if "{http://www.w3.org/XML/1998/namespace}id" not in node.attrib:
            raise ValueError("section missing xml:id attribute, line %d" %
                             node.sourceline)


def verify_attribute_profiling(doc, attribute, known_values):
    """Check for elements with attribute profiling set that conflicts with
       the attribute profiling of nodes below them in the DOM
       tree. This picks up cases where content is accidentally
       omitted via conflicting profiling. Checks known_values also for
       supported profiling values.
    """

    ns = {"docbook": "http://docbook.org/ns/docbook"}

    path = '//docbook:*[@%s]' % attribute
    for parent in doc.xpath(path, namespaces=ns):
        p_tag = parent.tag
        p_line = parent.sourceline
        p_att_list = parent.attrib[attribute].split(';')

        for att in p_att_list:
            if att not in known_values:
                raise ValueError(
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
                    raise ValueError(
                        "%s %s profiling (%s) conflicts with %s "
                        "profiling of %s on line %d." %
                        (p_tag[len_ns:], attribute, p_att_list,
                         attribute, c_tag[len_ns:], c_line))


def verify_profiling(doc):
    """"Check profiling information."""
    verify_attribute_profiling(doc, "os", KNOWN_OS_VALUES)
    verify_attribute_profiling(doc, "audience", KNOWN_AUDIENCE_VALUES)


def verify_nice_usage_of_whitespaces(docfile):
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
                                 % element)),
        checks.append(re.compile(".*[\w\-().:!?{}\[\]]+\s+<\/%s>.*\n"
                                 % element))

    lc = 0
    affected_lines = []
    tab_lines = []
    for line in open(docfile, 'r'):
        lc = lc + 1
        if '\t' in line:
            tab_lines.append(str(lc))

        for check in checks:
            if check.match(line) and lc not in affected_lines:
                affected_lines.append(str(lc))

    if len(affected_lines) > 0 and len(tab_lines) > 0:
        msg = "trailing or unnecessary whitespaces found in lines: %s" % (
              ", ".join(affected_lines))
        msg = msg + "; tabs found in lines: %s" % ", ".join(tab_lines)
        raise ValueError(msg)
    elif len(affected_lines) > 0:
        raise ValueError("trailing or unnecessary whitespaces found in "
                         "lines: %s" % (", ".join(affected_lines)))
    elif len(tab_lines) > 0:
        raise ValueError("tabs found in lines: %s" % ", ".join(tab_lines))


def error_message(error_log):
    """Return a string that contains the error message.

    We use this to filter out false positives related to IDREF attributes
    """
    errs = [str(x) for x in error_log if x.type_name != 'DTD_UNKNOWN_ID']

    # Reverse output so that earliest failures are reported first
    errs.reverse()
    return "\n".join(errs)


def only_www_touched():
    """Check whether only files in www directory are touched."""

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


def ha_guide_touched():
    """Check whether files in high-availability-guide directory are touched."""

    try:
        git_args = ["git", "diff", "--name-only", "HEAD~1", "HEAD"]
        modified_files = check_output(git_args).strip().split()
    except (subprocess.CalledProcessError, OSError) as e:
        print("git failed: %s" % e)
        sys.exit(1)

    ha_changed = False
    for f in modified_files:
        if f.startswith("doc/high-availability-guide/"):
            ha_changed = True

    return ha_changed


def check_modified_affects_all(rootdir, verbose):
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
        "tools/test.py",
        "doc/pom.xml"
    ]
    for f in modified_files:
        if f in special_files:
            if verbose:
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


def check_deleted_files(rootdir, file_exceptions, verbose):
    """Check whether files got deleted and verify that no other file
    references them.
    """

    print("Checking that no removed files are referenced...")
    deleted_files = get_modified_files(rootdir, "--diff-filter=D")
    if not deleted_files:
        print("No files were removed.\n")
        return

    if verbose:
        print(" Removed files:")
        for f in deleted_files:
            print ("   %s" % f)

    deleted_files = map(lambda x: os.path.abspath(x), deleted_files)
    no_checked_files = 0

    # Figure out whether files were included anywhere
    missing_reference = False

    for root, dirs, files in os.walk(rootdir):
        # Don't descend into 'target' subdirectories
        try:
            ind = dirs.index('target')
            del dirs[ind]
        except ValueError:
            pass

        # Filter out any dot directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        os.chdir(root)

        for f in files:
            if (f.endswith('.xml') and
                    f != 'pom.xml' and
                    f not in file_exceptions):
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
        print("Failed removed file check, %d files were removed, "
              "%d files checked.\n"
              % (len(deleted_files), no_checked_files))
        sys.exit(1)

    print("Passed removed file check, %d files were removed, "
          "%d files checked.\n"
          % (len(deleted_files), no_checked_files))


def validate_one_file(schema, rootdir, path, verbose,
                      check_syntax, check_niceness, validate_schema):
    """Validate a single file."""
    # We pass schema in as a way of caching it, generating it is expensive

    any_failures = False
    if verbose:
        print(" Validating %s" % os.path.relpath(path, rootdir))
    try:
        if check_syntax:
            doc = etree.parse(path)
            if validate_schema:
                if validation_failed(schema, doc):
                    any_failures = True
                    print(error_message(schema.error_log))
                verify_section_tags_have_xmid(doc)
                verify_profiling(doc)
        if check_niceness:
            verify_nice_usage_of_whitespaces(path)
    except etree.XMLSyntaxError as e:
        any_failures = True
        print("  %s: %s" % (os.path.relpath(path, rootdir), e))
    except ValueError as e:
        any_failures = True
        print("  %s: %s" % (os.path.relpath(path, rootdir), e))

    return any_failures


def is_xml(filename):
    """Returns true if file ends with .xml and is not a pom.xml file."""

    return filename.endswith('.xml') and not filename.endswith('/pom.xml')


def is_xml_like(filename):
    """Returns true if file is in some XML format we handle

    Skips pom.xml files as well since those are not handled.
    """

    return (filename.endswith(('.xml', '.xsd', '.xsl', '.wadl',
                               '.xjb')) and
            not filename.endswith('pom.xml'))


def is_wadl(filename):
    """Returns true if file ends with .wadl."""

    return filename.endswith('.wadl')


def validate_individual_files(files_to_check, rootdir, exceptions, verbose,
                              check_syntax=False, check_niceness=False,
                              ignore_errors=False, is_api_site=False):
    """Validate list of files."""

    schema = get_schema(is_api_site)
    if is_api_site:
        wadl_schema = get_wadl_schema()

    any_failures = False
    no_validated = 0
    no_failed = 0

    if check_syntax and check_niceness:
        print("Checking syntax and niceness of XML files...")
    elif check_syntax:
        print("Checking syntax of XML files...")
    elif check_niceness:
        print("Checking niceness of XML files...")

    for f in files_to_check:
        base_f = os.path.basename(f)
        if (base_f == "pom.xml" or
                base_f in exceptions):
            continue
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

        if (is_api_site and is_wadl(f)):
            any_failures = validate_one_file(wadl_schema, rootdir, f,
                                             verbose,
                                             check_syntax,
                                             check_niceness,
                                             validate_schema)
        else:
            any_failures = validate_one_file(schema, rootdir, f,
                                             verbose,
                                             check_syntax,
                                             check_niceness,
                                             validate_schema)
        if any_failures:
            no_failed = no_failed + 1
        no_validated = no_validated + 1

    if no_failed > 0:
        print("Check failed, validated %d XML files with %d failures.\n"
              % (no_validated, no_failed))
        if not ignore_errors:
            sys.exit(1)
    else:
        print("Check passed, validated %d XML files.\n" % no_validated)


def validate_modified_files(rootdir, exceptions, verbose,
                            check_syntax=False, check_niceness=False,
                            ignore_errors=False, is_api_site=False):
    """Validate list of modified files."""

    # Do not select deleted files, just Added, Copied, Modified, Renamed,
    # or Type changed
    modified_files = get_modified_files(rootdir, "--diff-filter=ACMRT")

    modified_files = filter(is_xml_like, modified_files)

    validate_individual_files(modified_files, rootdir, exceptions,
                              verbose,
                              check_syntax, check_niceness,
                              ignore_errors, is_api_site)


def validate_all_files(rootdir, exceptions, verbose,
                       check_syntax, check_niceness=False,
                       ignore_errors=False, is_api_site=False):
    """Validate all xml files."""

    files_to_check = []

    for root, dirs, files in os.walk(rootdir):
        # Don't descend into 'target' subdirectories
        try:
            ind = dirs.index('target')
            del dirs[ind]
        except ValueError:
            pass

        # Filter out any dot directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for f in files:
            # Ignore maven files, which are called pom.xml
            if (is_xml_like(f) and
                f not in exceptions):
                path = os.path.abspath(os.path.join(root, f))
                files_to_check.append(path)

    validate_individual_files(files_to_check, rootdir, exceptions,
                              verbose,
                              check_syntax, check_niceness,
                              ignore_errors, is_api_site)


def logging_build_book(result):
    """Callback for book building."""
    RESULTS_OF_BUILDS.append(result)


def build_book(book):
    """Build book(s) in directory book."""

    # Note that we cannot build in parallel several books in the same
    # directory like the Install Guide. Thus we build sequentially per
    # directory.
    os.chdir(book)
    result = True
    returncode = 0
    base_book = os.path.basename(book)
    try:
        # Clean first and then build so that the output of all guides
        # is available
        output = subprocess.check_output(
            ["mvn", "clean"],
            stderr=subprocess.STDOUT
        )
        if base_book == "install-guide":
            # Build Debian
            base_book = "install-guide (for debian)"
            output = subprocess.check_output(
                ["mvn", "generate-sources", "-B",
                 "-Doperating.system=apt-debian", "-Dprofile.os=debian"],
                stderr=subprocess.STDOUT
            )
            # Build Fedora
            base_book = "install-guide (for Fedora)"
            output = subprocess.check_output(
                ["mvn", "generate-sources", "-B",
                 "-Doperating.system=yum",
                 "-Dprofile.os=centos;fedora;rhel"],
                stderr=subprocess.STDOUT
            )
            # Build openSUSE
            base_book = "install-guide (for openSUSE)"
            output = subprocess.check_output(
                ["mvn", "generate-sources", "-B",
                 "-Doperating.system=zypper", "-Dprofile.os=opensuse;sles"],
                stderr=subprocess.STDOUT
            )
            # Build Ubuntu
            base_book = "install-guide (for Ubuntu)"
            output = subprocess.check_output(
                ["mvn", "generate-sources", "-B",
                 "-Doperating.system=apt", "-Dprofile.os=ubuntu"],
                stderr=subprocess.STDOUT
            )
            # Success
            base_book = "install-guide (for Debian, Fedora, openSUSE, Ubuntu)"
        elif base_book == "high-availability-guide":
            output = subprocess.check_output(
                ["build-ha-guide.sh", ],
                stderr=subprocess.STDOUT
            )
            output = subprocess.check_output(
                ["mvn", "generate-sources", "-B"],
                stderr=subprocess.STDOUT
            )
        # Repository: identity-api
        # Let's not check for "v3" but for the full name instead
        elif base_book.endswith("openstack-identity-api/v3"):
            output = subprocess.check_output(
                ["markdown-docbook.sh", "identity-api-v3"],
                stderr=subprocess.STDOUT
            )
            output = subprocess.check_output(
                ["mvn", "generate-sources", "-B"],
                stderr=subprocess.STDOUT
            )
        # Repository: image-api
        elif base_book == "openstack-image-service-api":
            output = subprocess.check_output(
                ["markdown-docbook.sh", "image-api-v2.0"],
                stderr=subprocess.STDOUT
            )
            output = subprocess.check_output(
                ["mvn", "generate-sources", "-B"],
                stderr=subprocess.STDOUT
            )
        else:
            output = subprocess.check_output(
                ["mvn", "generate-sources", "-B"],
                stderr=subprocess.STDOUT
            )
    except subprocess.CalledProcessError as e:
        output = e.output
        returncode = e.returncode
        result = False

    return (base_book, result, output, returncode)


def is_book_master(filename):
    """Returns True if filename is one of the special filenames used for the
    book master files.

    We do not parse pom.xml for the includes directive to determine
    the top-level files and thus have to use a heuristic.
    """

    return ((filename.startswith(('bk-', 'bk_', 'st-'))
             and filename.endswith('.xml')) or
            filename == 'openstack-glossary.xml')


def find_affected_books(rootdir, book_exceptions, verbose,
                        force, ignore_dirs):
    """Check which books are affected by modified files.

    Returns a set with books.
    """
    book_root = rootdir

    books = []
    affected_books = set()

    build_all_books = force or check_modified_affects_all(rootdir, verbose)

    # Dictionary that contains a set of files.
    # The key is a filename, the set contains files that include this file.
    included_by = {}

    # Dictionary with books and their bk*.xml files
    book_bk = {}

    # 1. Iterate over whole tree and analyze include files.
    # This updates included_by, book_bk and books.
    for root, dirs, files in os.walk(rootdir):
        # Don't descend into 'target' subdirectories
        try:
            ind = dirs.index('target')
            del dirs[ind]
        except ValueError:
            pass

        # Filter out any dot directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        # Filter out directories to be ignored
        if ignore_dirs:
            dirs[:] = [d for d in dirs if not d in ignore_dirs]

        if os.path.basename(root) in book_exceptions:
            break
        # Do not process files in doc itself or top-level directory
        elif root.endswith('doc') or root == rootdir:
            continue
        elif "pom.xml" in files:
            books.append(root)
            book_root = root

        # No need to check single books if we build all, we just
        # collect list of books
        if build_all_books:
            continue

        # ha-guide uses asciidoc which we do not track.
        # Just check whether any file is touched in that directory
        if root.endswith('doc/high-availability-guide'):
            if ha_guide_touched():
                affected_books.add(book_root)

        for f in files:
            f_base = os.path.basename(f)
            f_abs = os.path.abspath(os.path.join(root, f))
            if is_book_master(f_base):
                book_bk[f_abs] = book_root
            if (f.endswith('.xml') and
                    f != "pom.xml" and
                    f != "ha-guide-docinfo.xml"):
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

    if not build_all_books:
        # Generate list of modified_files
        # Do not select deleted files, just Added, Copied, Modified, Renamed,
        # or Type changed
        modified_files = get_modified_files(rootdir, "--diff-filter=ACMRT")
        modified_files = map(lambda x: os.path.abspath(x), modified_files)

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

    if build_all_books:
        print("Building all books.")
    elif affected_books:
        books = affected_books
    else:
        print("No books are affected by modified files. Building all books.")

    return books


def build_affected_books(rootdir, book_exceptions,
                         verbose, force=False, ignore_errors=False,
                         ignore_dirs=[]):
    """Build all the books which are affected by modified files.

    Looks for all directories with "pom.xml" and checks if a
    XML file in the directory includes a modified file. If at least
    one XML file includes a modified file the method calls
    "mvn clean generate-sources" in that directory.

    This will throw an exception if a book fails to build
    """

    books = find_affected_books(rootdir, book_exceptions,
                                verbose, force, ignore_dirs)

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
    for book in sorted(books):
        print("  %s" % os.path.basename(book))
        pool.apply_async(build_book, (book, ),
                         callback=logging_build_book)
    pool.close()
    print("Building all queued %d books now..." % len(books))
    pool.join()

    any_failures = False
    for book, result, output, returncode in RESULTS_OF_BUILDS:
        if result:
            print(">>> Build of book %s succeeded." % book)
        else:
            any_failures = True

    if any_failures:
        for book, result, output, returncode in RESULTS_OF_BUILDS:
            if not result:
                print(">>> Build of book %s failed (returncode = %d)."
                      % (book, returncode))
                print("\n%s" % output)

        print("Building of books finished with failures.\n")
        if not ignore_errors:
            sys.exit(1)
    else:
        print("Building of books finished successfully.\n")


def main():

    parser = argparse.ArgumentParser(description="Validate XML files against "
                                     "the DocBook 5 RELAX NG schema")
    parser.add_argument('path', nargs='?', default=default_root(),
                        help="Root directory that contains DocBook files, "
                        "defaults to `git rev-parse --show-toplevel`")
    parser.add_argument("--force", help="Force the validation of all files "
                        "and build all books", action="store_true")
    parser.add_argument("--check-build", help="Try to build books using "
                        "modified files", action="store_true")
    parser.add_argument("--check-syntax", help="Check the syntax of modified "
                        "files", action="store_true")
    parser.add_argument("--check-deletions", help="Check that deleted files "
                        "are not used.", action="store_true")
    parser.add_argument("--check-niceness", help="Check the niceness of "
                        "files, for example whitespace.",
                        action="store_true")
    parser.add_argument("--check-all", help="Run all checks "
                        "(default if no arguments are given)",
                        action="store_true")
    parser.add_argument("--ignore-errors", help="Do not exit on failures",
                        action="store_true")
    parser.add_argument("--verbose", help="Verbose execution",
                        action="store_true")
    parser.add_argument("--api-site", help="Special handling for "
                        "api-site repository",
                        action="store_true")
    parser.add_argument("--ignore-dir",
                        help="Directory to ignore for building of "
                        "manuals. The parameter can be passed multiple "
                        "times to add several directories.",
                        action="append")
    parser.add_argument('--version',
                        action='version',
                        version=os_doc_tools.__version__)

    prog_args = parser.parse_args()

    print ("OpenStack Doc Checks (using openstack-doc-tools version %s)\n"
           % os_doc_tools.__version__)
    if not prog_args.api_site:
        prog_args.path = os.path.join(prog_args.path, 'doc')
    if (len(sys.argv) == 1):
        # No arguments given, use check-all
        prog_args.check_all = True

    if prog_args.check_all:
        prog_args.check_deletions = True
        prog_args.check_syntax = True
        prog_args.check_build = True
        prog_args.check_niceness = True

    if not prog_args.force and only_www_touched():
        print("Only files in www directory changed, nothing to do.\n")
        return

    if prog_args.check_syntax or prog_args.check_niceness:
        if prog_args.force:
            validate_all_files(prog_args.path, FILE_EXCEPTIONS,
                               prog_args.verbose,
                               prog_args.check_syntax,
                               prog_args.check_niceness,
                               prog_args.ignore_errors,
                               prog_args.api_site)
        else:
            validate_modified_files(prog_args.path, FILE_EXCEPTIONS,
                                    prog_args.verbose,
                                    prog_args.check_syntax,
                                    prog_args.check_niceness,
                                    prog_args.ignore_errors,
                                    prog_args.api_site)

    if prog_args.check_deletions:
        check_deleted_files(prog_args.path, FILE_EXCEPTIONS, prog_args.verbose)

    if prog_args.check_build:
        build_affected_books(prog_args.path, BOOK_EXCEPTIONS,
                             prog_args.verbose, prog_args.force,
                             prog_args.ignore_errors,
                             prog_args.ignore_dir)


def default_root():
    """Return the location of openstack-manuals

    The current working directory must be inside of the openstack-manuals
    repository for this method to succeed
    """

    try:
        git_args = ["git", "rev-parse", "--show-toplevel"]
        gitroot = check_output(git_args).rstrip()
    except (subprocess.CalledProcessError, OSError) as e:
        print("git failed: %s" % e)
        sys.exit(1)

    return gitroot

if __name__ == "__main__":
    sys.exit(main())
