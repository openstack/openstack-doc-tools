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
