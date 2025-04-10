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

import re
import time
import urllib.parse as urlparse

from scrapy import item
from scrapy import linkextractors
from scrapy import spiders


class SitemapItem(item.Item):
    '''Class to represent an item in the sitemap.'''
    loc = item.Field()
    lastmod = item.Field()
    priority = item.Field()
    changefreq = item.Field()


class SitemapSpider(spiders.CrawlSpider):
    name = 'sitemap'

    MAINT_SERIES = [
        '2023.2',
        '2024.1',
        '2024.2',
        '2025.1',
    ]
    MAINT_RELEASES_PAT = re.compile('^.*/(' + '|'.join(MAINT_SERIES) + ')/')
    LATEST_PAT = re.compile('^.*/latest/')

    rules = [
        spiders.Rule(
            linkextractors.LinkExtractor(
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
                    r'/austin/',
                    r'/bexar/',
                    r'/cactus/',
                    r'/diablo/',
                    r'/essex/',
                    r'/folsom/',
                    r'/grizzly/',
                    r'/havana/',
                    r'/icehouse/',
                    r'/juno/',
                    r'/kilo/',
                    r'/liberty/',
                    r'/mitaka/',
                    r'/newton/',
                    r'/ocata/',
                    r'/pike/',
                    r'/queens/',
                    r'/rocky/',
                    r'/stein/',
                    r'/train/',
                    r'/ussuri/',
                    r'/victoria/',
                    r'/wallaby/',
                    r'/xena/',
                    r'/yoga/',
                ],
                deny_domains=[
                    # docs.o.o redirects to a few sites, filter
                    # them out
                    'docs.opendev.org',
                    'opendev.org',
                    'releases.openstack.org',
                    'zuul-ci.org',
                ]
            ),
            follow=True, callback='parse_item'
        )
    ]

    def __init__(self, domain='docs.openstack.org', urls='', *args, **kwargs):
        super(SitemapSpider, self).__init__(*args, **kwargs)
        self.domain = domain
        self.allowed_domains = [domain]
        self.start_urls = ['https://%s' % domain]
        for url in urls.split(','):
            if not url:
                continue
            self.start_urls.append(url)

    def parse_item(self, response):
        item = SitemapItem()
        item['loc'] = response.url

        components = urlparse.urlsplit(response.url)

        # Filter out any redirected URLs to other domains
        if self.domain != components.netloc:
            return

        if self.MAINT_RELEASES_PAT.match(components.path):
            # weekly changefrequency and highest prio for maintained release
            item['priority'] = '1.0'
            item['changefreq'] = 'weekly'
        elif self.LATEST_PAT.match(components.path):
            # daily changefrequency and normal priority for current files
            item['priority'] = '0.5'
            item['changefreq'] = 'daily'
        else:
            # These are unversioned documents
            # daily changefrequency and highest priority for current files
            item['priority'] = '1.0'
            item['changefreq'] = 'daily'

        if 'Last-Modified' in response.headers:
            timestamp = response.headers['Last-Modified']
        else:
            timestamp = response.headers['Date']
        lastmod = time.strptime(timestamp.decode("utf-8"),
                                "%a, %d %b %Y %H:%M:%S %Z")
        item['lastmod'] = time.strftime("%Y-%m-%dT%H:%M:%S%z", lastmod)
        return item
