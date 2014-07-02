OpenStack Doc Tools
*******************

This repository contains tools used by the OpenStack Documentation
project.

For more details, see the `OpenStack Documentation wiki page
<http://wiki.openstack.org/Documentation>`_.

Prerequisites
=============
`Apache Maven <http://maven.apache.org/>`_ must be installed to build the
documentation.

To install Maven 3 for Ubuntu 12.04 and later, and Debian wheezy and later::

    apt-get install maven

On Fedora::

    yum install maven3

This package needs a few external dependencies including lxml. If you
do not have lxml installed, you can either install python-lxml or have
it installed automatically and build from sources. To build lxml from
sources, you need a C compiler and the xml and xslt development
packages installed.

To install python-lxml, execute the following based on your
distribution.

On Fedora::

    yum install python-lxml

On openSUSE::

    zypper in python-lxml

On Ubuntu::

    apt-get install python-lxml

For building from source,  install the dependencies of lxml.

On openSUSE::

    zypper in libxslt-devel

On Ubuntu::

    apt-get install libxml2-dev libxslt-dev


Updating RNG schema files
=========================

The repository contains in the directory ``os_doc_tools/resources`` a
local copy of some RNG schema files so that they do not need to be
downloaded each time for validation of XML and WADL files.

Please see the ``README.txt`` in the directory for details on where
these files come from.

Publishing of books
===================
If you run the ``openstack-doc-test --check-build``, it will copy all
the books to the directory ``publish-docs`` in the top-level directory
of your repository.

By default, it outputs a directory with the same name as the directory
where the pom.xml file lives in, such as admin-guide-cloud. You can
also check the output of the build job for the name.

Some books need special treatment and there are three options you can
set in the file ``doc-test.conf``:

 * ``book`` - the name of a book that needs special treatment
 * ``target_dir`` - the path of subdirectory starting at ``target``
   that is the root for publishing
 * ``publish_dir`` - a new name to publish a book under

As an example, to publish the compute-api version 2 in the directory
``publish-docs/api/openstack-compute/2``, use::

  book = openstack-compute-api-2
  target_dir = target/docbkx/webhelp/api/openstack-compute/2
  publish_dir = api/openstack-compute/2

Note that these options can be specified multiple times and should
always be used this way. You do not need to set ``publish_dir`` but if
you set it, you need to use it every time.

Also note that these are optional settings, the logic in the tool is
sufficient for many of the books.

Release notes
=============

0.16.1
------

* Fix includes of rackbook.rng to unbreak syntax checking.

0.16
----

* ``openstack-doc-test``: Fix handling of ignore-dir parameter.
* ``autohelp-wrapper``: New tool to simplify the setup of an autohelp.py
  environment.
* ``diff_branches.py``: Generates a listing of the configuration options
  changes that occured between 2 openstack releases.
* ``autohelp.py``: Add the 'dump' subcommand, include swift.
* ``jsoncheck.py``: Add public API.
* Added tool to generate a sitemap.xml file.
* Added script to prettify HTML and XML syntax.

0.15
----

* ``openstack-doc-test``: Output information about tested patch,
  special case entity files for book building. Remove special handling
  for high-availability-guide, it is not using asciidoc anymore.
* New script in cleanup/retf for spell checking using the RETF rules.
  patch.
* Fix entity handling in ``openstack-generate-docbook``.

0.14
----

* ``openstack-auto-commands``: Improved screen generation and swift
  subcommand xml output.
* ``openstack-doc-test``: Warn about non-breaking space, enhance
  -v output, special case building of localized high-availability
  guide, fix for building changed identity-api repository.
* New command ``openstack-jsoncheck`` to check for niceness of JSON
  files and reformat them.
* ``openstack-autohelp``: Update the default parameters. The tables
  are generated in the doc/common/tables/ dir by default, and the git
  repository for the project being worked on is looked at in a sources/
  dir by default.


0.13
----

* ``extract_swift_flags``: Correctly parses existing tables and
  improve the output to ease the tables edition.
* ``openstack-generate-docbook`` handles now the api-site project:
  Parameter --root gives root directory to use.
* Remove obsoleted commands ``generatedocbook`` and
  ``generatepot``. They have been obsoleted in 0.7.

0.12
----

* ``openstack-doc-test``: Handle changes in api-site project, new
  option --print-unused-files.
* ``openstack-autohelp``: Handle keystone_authtoken options.

0.11
----

* Add ``--publish`` option to ``openstack-doc-test`` that does not
  publish the www directory to the wrong location.
* Improvements for generation of option tables.

0.10
----

* Fix ``openstack-doc-test`` to handle changes in ``api-site`` repository:
  Do not publish wadls directory, *.fo files and add api-ref-guides
  PDF files to index file for docs-draft.
* Many improvements for generation of option tables.
* Improvements for ``openstack-auto-commands``: handle ironic, sahara;
  improve generated output.

0.9
---

Fixes for openstack-doc-test:

* openstack-doc-test now validates JSON files for well-formed-ness and whitespace.
* Create proper chapter title for markdown files.
* Ignore publish-docs directory completely.
* Do not check for xml:ids in wadl resource.
* New option build_file_excepetion to ignore invalid XML files for
  dependency checking in build and syntax checks.

Fixes for autodoc-tools to sanitize values and handle projects.

Client version number is output by openstack-auto-commands.

0.8.2
-----

Fixes for openstack-doc-test:

* Fix error handling, now really abort if an error occurs.
* Avoid races in initial maven setup that broke build.
* Add --parallel/noparallel flags to disable parallel building.

0.8.1
-----

* Fix openstack-doc-test building of image-api.
* Fix publishing of api-ref.
* Improve markdown conversion.

0.8
---

* Improved openstack-auto-commands output
* Fix script invocation in openstack-doc-test.

0.7.1
-----

* Fix openstack-doc-test niceness and syntax checks that always
  failed in api projects.
* Fix building of image-api-v2

0.7
---

* openstack-doc-test:

   - Fix building of identity-api and image-api books.
   - Add option --debug.
   - Generate log file for each build.
   - Do not install build-ha-guide.sh and markdown-docbook.sh in
     /usr/bin, use special scripts dir instead.
   - Allow to configure the directory used under publish-doc

* generatedocbook and generatepot have been merged into a single
  file, the command has been renamed to
  openstack-generate-docbook/openstack-generate-pot.  For
  compatibility, wrapper scripts are installed that will be removed
  in version 0.8.

0.6
---

* Fix python packaging bugs that prevented sitepackages usage and
  installed .gitignore in packages

0.5
---

* Test that resources in wadl files have an xml:id (lp:bug 1275007).
* Improve formatting of python command line clients (lp:bug 1274699).
* Copy all generated books to directory publish-docs in the git
  top-level (lp:blueprint draft-docs-on-docs-draft).
* Requires now a config file in top-level git directory named
  doc-test.conf.
* Allow building of translated manuals, these need to be setup first
  with "generatedocbook -l LANGUAGE -b BOOK".

0.4
---

* New option --exceptions-file to pass list of files to ignore
  completely.
* Major improvements for automatic generation of option tables.
* New tool openstack-auto-commands to document python
  command line clients.

0.3
---

* Fixes path for automated translation toolchain to fix lp:bug 1216153.
* Validates .xsd .xsl and.xjb files in addition to .xml.
* Fixes validation of WADL files to validate properly against XML schema.

0.2
---

* Enables local copies of RNG schema for validation.
* Enables ignoring directories when checking.

0.1
---

Initial release.

Contributing
============
Our community welcomes all people interested in open source cloud computing,
and encourages you to join the `OpenStack Foundation <http://www.openstack.org/join>`_.
The best way to get involved with the community is to talk with others online
or at a meetup and offer contributions through our processes, the `OpenStack
wiki <http://wiki.openstack.org>`_, blogs, or on IRC at ``#openstack``
on ``irc.freenode.net``.

We welcome all types of contributions, from blueprint designs to documentation
to testing to deployment scripts.

If you would like to contribute to the development,
you must follow the steps in the "If you're a developer, start here"
section of this page:

   http://wiki.openstack.org/HowToContribute

Once those steps have been completed, changes to OpenStack
should be submitted for review via the Gerrit tool, following
the workflow documented at:

   http://wiki.openstack.org/GerritWorkflow

Pull requests submitted through GitHub will be ignored.

Bugs should be filed on Launchpad, not GitHub:

   https://bugs.launchpad.net/openstack-manuals
