Release notes
=============

0.29.1
------

* ``doc-tools-check-languages``: Fix building of translated RST guides.

0.29.0
------

* ``doc-tools-check-languages``: Handle common-rst directory, update
  for User Guides and firstapp.
* ``autohelp.py``: Suport generation of RST tables, fixes for
  extensions.

0.28
----

* ``openstack-doc-test``: Sort entries in index.html file.
* ``diff_branches.py``: Add options containing DEPRECATED in their help
  string to the deprecation list.
* ``doc-tools-check-languages``: Fix bugs in RST handling that broke
  handling of user-guide and user-guide-admin.

0.27
----

* ``openstack-doc-test``: Do not build Debian Install Guide by
  default, built it only if the parameter ``--enable-debian-install``
  is passed. Fix index.html file and remove
  www files that came in by accident.

0.26
----

* Fix ``doc-tools-check-languages`` handling of RST guides and
  publishing to translated draft guides.
* Improve ``openstack-auto-commands``: bash-completion support for
  python-glanceclient, new commands for python-swiftclient, new command
  for trove-manage, automatically identify deprecated subcommands,
  move client definitions into a YAML resource file, support of the
  complete subcommand, support for new clients (barbican, designate, manila,
  magnetodb, manila, mistral, tuskar).

0.25
----

* Enhance ``doc-tools-check-languages`` to handle translation of RST
  guides and publishing of draft guides to /draft/.
* ``autohelp.py``: lookup configuration options in more oslo libraries.
* ``autohelp.py``: add a hook for neutron plugins
* ``autohelp-wrapper``: improve reliability by building a virtual env per
  project, rather than a common virtual env.
* ``autohelp-wrapper``: define the custom dependencies for each project in
  their own requirements files.

0.24
----

* Added ``doc-tools-update-cli-reference``, a wrapper script to update
  CLI references in the ``openstack-manuals`` repository.
* Handle guides that published without a content/ sub directory.
* Various fixes for auto generating commands and options.
* Handle translation of RST guides.

0.23
----

* ``openstack-doc-test``: Don't build all books if only RST files are
  changed.

0.22
----

* ``openstack-doc-test``: New niceness check to avoid specific unicode
  characters; new option --ignore-book to not build a book.

0.21.1
------

* ``jsoncheck``: have formatted JSON files end with a newline (lp:bug 1403159)

0.21
----

* ``openstack-doc-test``: New option ``--url-exception`` to ignore
  URLs in link check. Use jsoncheck in tests for more better tests and
  output.
* ``openstack-auto-commands``: Update list of supported commands to
  include ironic, sahara
* ``openstack-dn2osdbk``: Various fixes.

0.20
----

* ``openstack-doc-test``: Check for a ``\n`` in the last line of a file.
* ``openstack-dn2osdbk``: Properly handle internal references.

0.19
----

* ``openstack-doc-test``: Optimize translation imports, improve output
  messages.
* ``autohelp.py``: Improve sanitizer, better support for i18n in
  projects, allow setting of title name for tables.
* ``autohelp-wrapper``: Smarter handling of the manuals repo and environment
  setup, add support for the ``create`` subcommand.
* ``autohelp-wrapper``: Add support for offline/fast operation.
* ``autohelp-wrapper``: Add a module blacklisting mechanism.
* ``diff_branches.py``: Updated output format.
* Provide a ``hotref`` extension for sphinx, to automate the creation of
  references to the HOT resources documentation.
* ``openstack-auto-commands``: Handle python-openstackclient, handle
  python-glanceclient and python-cinderclient v2 commands.

0.18.1
------

* Fix ``doc-tools-check-languages`` to handle all repositories and
  setups.

0.18
----

* ``openstack-doc-test``: Don't always build the HOT guide, add new
  option --check-links to check for valid URLs.
* ``openstack-dn2osdbk``: Allow single files as source.
* Imported and improved ``doc-tools-check-languages`` (recently known
  as ``tools/test-languages.sh`` in the documentation repositories).
* Added a virtual build and test environment based on Vagrant.

0.17
----

* Added support for ``*-manage`` CLI doc generation.
* ``openstack-dn2osdbk``: Converts Docutils Native XML to docbook.
* ``openstack-doc-test``: Handle the upcoming HOT guide.
* ``autohelp.py``: Provide our own sanitizer.
* ``autohelp.py``: Use the oslo sample_default if available.
* ``openstack-doc-test``: Correctly handle SIGINT.
* Various smaller fixes and improvements.

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
  Do not publish wadls directory, ``*.fo`` files and add api-ref-guides
  PDF files to index file for docs-draft.
* Many improvements for generation of option tables.
* Improvements for ``openstack-auto-commands``: handle ironic, sahara;
  improve generated output.

0.9
---

Fixes for openstack-doc-test:

* openstack-doc-test now validates JSON files for well-formed-ness and
  whitespace.
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
