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

import scrapy
from sitemap.generator.spiders import sitemap_file
import unittest
from unittest import mock


class TestSitemapItem(unittest.TestCase):

    def test_class_type(self):
        self.assertTrue(type(sitemap_file.SitemapItem) is scrapy.item.ItemMeta)

    def test_class_supports_fields(self):
        with mock.patch.object(scrapy.item, 'Field'):
            a = sitemap_file.SitemapItem()

        supported_fields = ['loc', 'lastmod', 'priority', 'changefreq']
        for field in supported_fields:
            a[field] = field

        not_supported_fields = ['some', 'random', 'fields']
        for field in not_supported_fields:
            with self.assertRaises(KeyError):
                a[field] = field


class TestSitemapSpider(unittest.TestCase):

    def setUp(self):
        self.spider = sitemap_file.SitemapSpider()

    def test_set_vars_on_init(self):
        domain = 'docs.openstack.org'
        self.assertEqual(self.spider.domain, domain)
        self.assertEqual(self.spider.allowed_domains, [domain])
        self.assertEqual(self.spider.start_urls, ['https://%s' % domain])

    def test_start_urls_get_appended(self):
        urls = 'new.openstack.org, old.openstack.org'
        urls_len = len(urls.split(','))
        spider_len = len(self.spider.start_urls)

        spider_with_urls = sitemap_file.SitemapSpider(urls=urls)
        spider_with_urls_len = len(spider_with_urls.start_urls)

        self.assertEqual(spider_with_urls_len, (urls_len + spider_len))

    def test_parse_items_inits_sitemap(self):
        response = mock.MagicMock()
        path = sitemap_file.urlparse.SplitResult(
            scheme='https',
            netloc='docs.openstack.org',
            path='/ocata/something.html',
            query='',
            fragment=''
        )
        with mock.patch.object(sitemap_file,
                               'SitemapItem') as mocked_sitemap_item:
            with mock.patch.object(sitemap_file.urlparse, 'urlsplit',
                                   return_value=path):
                with mock.patch.object(sitemap_file, 'time'):
                    self.spider.parse_item(response)

        self.assertTrue(mocked_sitemap_item.called)

    def test_parse_items_gets_path(self):
        response = mock.MagicMock()
        path = sitemap_file.urlparse.SplitResult(
            scheme='https',
            netloc='docs.openstackorg',
            path='/ocata/something.html',
            query='',
            fragment=''
        )
        with mock.patch.object(sitemap_file, 'SitemapItem'):
            with mock.patch.object(sitemap_file.urlparse,
                                   'urlsplit',
                                   return_value=path) as mocked_urlsplit:
                with mock.patch.object(sitemap_file, 'time'):
                    self.spider.parse_item(response)

        self.assertTrue(mocked_urlsplit.called)

    def test_parse_items_low_priority_weekly_freq(self):
        response = mock.MagicMock()
        path = sitemap_file.urlparse.SplitResult(
            scheme='https',
            netloc='docs.openstack.org',
            path='/ocata/something.html',
            query='',
            fragment=''
        )
        with mock.patch.object(sitemap_file.urlparse, 'urlsplit',
                               return_value=path):
            with mock.patch.object(sitemap_file, 'time'):
                returned_item = self.spider.parse_item(response)

        self.assertEqual('1.0', returned_item['priority'])
        self.assertEqual('weekly', returned_item['changefreq'])

    def test_parse_items_high_priority_daily_freq(self):
        response = mock.MagicMock()
        path = sitemap_file.urlparse.SplitResult(
            scheme='https',
            netloc='docs.openstack.org',
            path='/contributor-guide',
            query='',
            fragment=''
        )
        with mock.patch.object(sitemap_file.urlparse, 'urlsplit',
                               return_value=path):
            with mock.patch.object(sitemap_file, 'time'):
                returned_item = self.spider.parse_item(response)

        self.assertEqual('1.0', returned_item['priority'])
        self.assertEqual('daily', returned_item['changefreq'])

    def test_parse_returns_populated_item(self):
        response = mock.MagicMock()
        path = sitemap_file.urlparse.SplitResult(
            scheme='https',
            netloc='docs.openstack.org',
            path='/ocata',
            query='',
            fragment=''
        )
        with mock.patch.object(sitemap_file.urlparse, 'urlsplit',
                               return_value=path):
            with mock.patch.object(sitemap_file, 'time'):
                returned_item = self.spider.parse_item(response)

        self.assertEqual(4, len(returned_item))


if __name__ == '__main__':
    unittest.main()
