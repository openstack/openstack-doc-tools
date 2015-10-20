Sitemap Generator
*****************

This script crawls all available sites on http://docs.openstack.org and extracts
all URLs. Based on the URLs the script generates a sitemap for search engines
according to the protocol described at http://www.sitemaps.org/protocol.html.

Usage
=====

To generate a new sitemap file simply run the spider using the
following command. It will take several minutes to crawl all available sites
on http://docs.openstack.org. The result will be available in the file
``sitemap_docs.openstack.org.xml``.

    $ scrapy crawl sitemap

It's also possible to crawl other sites using the attribute ``domain``.

For example to crawl http://developer.openstack.org use the following command.
The result will be available in the file ``sitemap_developer.openstack.org.xml``.

    $ scrapy crawl sitemap -a domain=developer.openstack.org

To write log messages into a file append the parameter ``-s LOG_FILE=scrapy.log``.

It is possible to define a set of additional start URLs using the attribute
``urls``. Separate multiple URLs with ``,``.

    $ scrapy crawl sitemap -a domain=developer.openstack.org -a urls="http://developer.openstack.org/de/api-guide/quick-start/"

Dependencies
============

* `Scrapy <https://pypi.python.org/pypi/Scrapy>`_

To install the needed modules you can use pip or the package management system included
in your distribution. When using the package management system maybe the name of the
packages differ. When using pip it's maybe necessary to install some development packages.

    $ pip install -r requirements.txt
