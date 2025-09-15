===================
OpenStack Doc Tools
===================

.. image:: https://governance.openstack.org/tc/badges/openstack-doc-tools.svg

.. Change things from this point on

This repository contains tools used by the OpenStack Documentation
project.

For more details, see the `OpenStack Documentation Contributor Guide
<https://docs.openstack.org/contributor-guide/>`_.

* License: Apache License, Version 2.0
* Source: https://opendev.org/openstack/openstack-doc-tools
* Bugs: https://bugs.launchpad.net/openstack-doc-tools

Prerequisites
-------------

You need to have Python 3 installed for using the tools.

This package needs a few external dependencies including lxml. If you
do not have lxml installed, you can either install python3-lxml or have
it installed automatically and build from sources. To build lxml from
sources, you need a C compiler and the xml and xslt development
packages installed.

To install python-lxml, execute the following based on your
distribution.

On Fedora, RHEL and CentOS Stream::

    $ dnf install python3-lxml

On Ubuntu::

    $ apt-get install python3-lxml

For building from source,  install the dependencies of lxml.

On Fedora, RHEL and CentOS Stream::

    $ dnf install python3-devel libxml2-devel libxslt-devel

On Ubuntu::

    $ apt-get install libxml2-dev libxslt-dev
