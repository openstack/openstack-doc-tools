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

    yum install maven

You need to have Python 2.7 installed for using the tools.

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

On Fedora::

    yum install python-devel libxml2-devel libxslt-devel

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

* License: Apache License, Version 2.0
* Source: http://git.openstack.org/cgit/openstack/openstack-doc-tools
* Bugs: http://bugs.launchpad.net/openstack-manuals
