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
