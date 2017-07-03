=================
Sitemap Generator
=================

This script crawls all available sites on http://docs.openstack.org and
extracts all URLs. Based on the URLs the script generates a sitemap for search
engines according to the `sitemaps protocol
<http://www.sitemaps.org/protocol.html>`_.

Installation
~~~~~~~~~~~~

To install the needed modules you can use pip or the package management system
included in your distribution. When using the package management system maybe
the name of the packages differ. Installation in a virtual environment is
recommended.

.. code-block:: console

   $ virtualenv venv
   $ source venv/bin/activate
   $ pip install Scrapy

When using pip, you may also need to install some development packages. For
example, on Ubuntu 16.04 install the following packages:

.. code-block:: console

   $ sudo apt install gcc libssl-dev python-dev python-virtualenv

Usage
~~~~~

To generate a new sitemap file, change into your local clone of the
``openstack/openstack-doc-tools`` repository and run the following commands:

.. code-block:: console

   $ cd sitemap
   $ scrapy crawl sitemap

The script takes several minutes to crawl all available
sites on http://docs.openstack.org. The result is available in the
``sitemap_docs.openstack.org.xml`` file.

Options
~~~~~~~

domain=URL

   Sets the ``domain`` to crawl. Default is ``docs.openstack.org``.

   For example, to crawl http://developer.openstack.org use the following
   command:

   .. code-block:: console

      $ scrapy crawl sitemap -a domain=developer.openstack.org

   The result is available in the ``sitemap_developer.openstack.org.xml`` file.

urls=URL

   You can define a set of additional start URLs using the ``urls`` attribute.
   Separate multiple URLs with ``,``.

   For example:

   .. code-block:: console

      $ scrapy crawl sitemap -a domain=developer.openstack.org -a urls="http://developer.openstack.org/de/api-guide/quick-start/"

LOG_FILE=FILE

   Write log messages to the specified file.

   For example, to write to ``scrapy.log``:

   .. code-block:: console

      $ scrapy crawl sitemap -s LOG_FILE=scrapy.log
