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

import posixpath
import time
import urlparse

from generator import items
from scrapy.linkextractors import LinkExtractor
from scrapy import spiders


class SitemapSpider(spiders.CrawlSpider):
    name = 'sitemap'

    rules = [
        spiders.Rule(
            LinkExtractor(
                allow=[
                    r'.*\.html',
                    r'.*\.pdf',
                    r'.*\.xml',
                    r'.*\.txt',
                    r'.*/',
                ],
                deny=[
                    r'/trunk/',
                    r'/draft/',
                    r'/api/'
                ]
            ),
            follow=True, callback='parse_item'
        )
    ]

    def __init__(self, domain='docs.openstack.org', urls='', *args, **kwargs):
        super(SitemapSpider, self).__init__(*args, **kwargs)
        self.domain = domain
        self.allowed_domains = [domain]
        self.start_urls = ['http://%s/index.html' % domain]
        for url in urls.split(','):
            self.start_urls.append(url)

    def parse_item(self, response):
        item = items.SitemapItem()
        item['priority'] = '0.5'
        item['changefreq'] = 'daily'
        item['loc'] = response.url

        path = urlparse.urlsplit(response.url).path
        filename = posixpath.basename(path)

        if filename == 'index.html' or filename == '':
            item['priority'] = '1.0'

        weekly = [
            'juno',
            'icehouse',
            'havana'
        ]

        for entry in weekly:
            if path.startswith("/%s" % entry):
                item['changefreq'] = 'weekly'

        if 'Last-Modified' in response.headers:
            timestamp = response.headers['Last-Modified']
        else:
            timestamp = response.headers['Date']
        lastmod = time.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %Z")
        item['lastmod'] = time.strftime("%Y-%m-%dT%H:%M:%S%z", lastmod)
        return item
