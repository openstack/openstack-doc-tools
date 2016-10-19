OpenStack Doc Tools
*******************

This repository contains tools used by the OpenStack Documentation
project.

For more details, see the `OpenStack Documentation wiki page
<http://wiki.openstack.org/Documentation>`_.

Prerequisites
=============

You need to have Python 2.7 installed for using the tools.

This package needs a few external dependencies including lxml. If you
do not have lxml installed, you can either install python-lxml or have
it installed automatically and build from sources. To build lxml from
sources, you need a C compiler and the xml and xslt development
packages installed.

To install python-lxml, execute the following based on your
distribution.

On Fedora::

    $ yum install python-lxml

On openSUSE::

    $ zypper in python-lxml

On Ubuntu::

    $ apt-get install python-lxml

For building from source,  install the dependencies of lxml.

On Fedora::

    $ yum install python-devel libxml2-devel libxslt-devel

On openSUSE::

    $ zypper in libxslt-devel

On Ubuntu::

    $ apt-get install libxml2-dev libxslt-dev


* License: Apache License, Version 2.0
* Source: http://git.openstack.org/cgit/openstack/openstack-doc-tools
* Bugs: http://bugs.launchpad.net/openstack-manuals
