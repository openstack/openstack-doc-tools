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

import mock
from sitemap.generator import pipelines
import unittest


class TestSitemapItemExporter(unittest.TestCase):

    def test_start_exporting(self):
        output = mock.MagicMock()
        itemExplorer = pipelines.SitemapItemExporter(output)

        with mock.patch.object(itemExplorer.xg, 'startDocument',
                               return_value=None) as mock_start_document:
            with mock.patch.object(itemExplorer.xg, 'startElement',
                                   return_value=None) as mock_start_element:
                itemExplorer.start_exporting()

        self.assertTrue(mock_start_document.called)
        self.assertTrue(mock_start_element.called)


class TestIgnoreDuplicateUrls(unittest.TestCase):

    def setUp(self):
        self.ignore_urls = pipelines.IgnoreDuplicateUrls()

    def test_set_is_set_at_init(self):
        self.assertTrue(isinstance(self.ignore_urls.processed, set))

    def test_set_is_empty_at_init(self):
        self.assertEqual(len(self.ignore_urls.processed), 0)

    def test_duplicate_url(self):
        self.ignore_urls.processed.add('url')
        item = {'loc': 'url'}
        spider = mock.MagicMock()

        with self.assertRaises(pipelines.scrapy.exceptions.DropItem):
            self.ignore_urls.process_item(item, spider)

    def test_url_added_to_processed(self):
        self.assertFalse('url' in self.ignore_urls.processed)

        item = {'loc': 'url'}
        spider = mock.MagicMock()
        self.ignore_urls.process_item(item, spider)
        self.assertTrue('url' in self.ignore_urls.processed)

    def test_item_is_returned(self):
        item = {'loc': 'url'}
        spider = mock.MagicMock()
        returned_item = self.ignore_urls.process_item(item, spider)
        self.assertEqual(item, returned_item)


class TestExportSitemap(unittest.TestCase):

    def setUp(self):
        self.export_sitemap = pipelines.ExportSitemap()
        self.spider = mock.MagicMock()

    def test_variables_set_at_init(self):
        self.assertTrue(isinstance(self.export_sitemap.files, dict))
        self.assertTrue(self.export_sitemap.exporter is None)

    def test_spider_opened_calls_open(self):
        with mock.patch.object(pipelines, 'open',
                               return_value=None) as mocked_open:
            with mock.patch.object(pipelines,
                                   'SitemapItemExporter'):
                self.export_sitemap.spider_opened(self.spider)

        self.assertTrue(mocked_open.called)

    def test_spider_opened_assigns_spider(self):
        prev_len = len(self.export_sitemap.files)
        with mock.patch.object(pipelines, 'open',
                               return_value=None):
            with mock.patch.object(pipelines,
                                   'SitemapItemExporter'):
                self.export_sitemap.spider_opened(self.spider)

        after_len = len(self.export_sitemap.files)
        self.assertTrue(after_len - prev_len, 1)

    def test_spider_opened_instantiates_exporter(self):
        with mock.patch.object(pipelines, 'open',
                               return_value=None):
            with mock.patch.object(pipelines,
                                   'SitemapItemExporter') as mocked_exporter:
                self.export_sitemap.spider_opened(self.spider)

        self.assertTrue(mocked_exporter.called)

    def test_spider_opened_exporter_starts_exporting(self):
        with mock.patch.object(pipelines, 'open',
                               return_value=None):
            with mock.patch.object(pipelines.SitemapItemExporter,
                                   'start_exporting') as mocked_start:
                self.export_sitemap.spider_opened(self.spider)

        self.assertTrue(mocked_start.called)

    def test_spider_closed_calls_finish(self):
        self.export_sitemap.exporter = mock.MagicMock()
        self.export_sitemap.exporter.finish_exporting = mock.MagicMock()
        self.export_sitemap.files[self.spider] = mock.MagicMock()

        with mock.patch.object(pipelines, 'lxml'):
            with mock.patch.object(pipelines, 'open'):
                self.export_sitemap.spider_closed(self.spider)

        self.assertTrue(self.export_sitemap.exporter.finish_exporting.called)

    def test_spider_closed_pops_spider(self):
        self.export_sitemap.exporter = mock.MagicMock()
        self.export_sitemap.files[self.spider] = mock.MagicMock()

        self.assertTrue(self.spider in self.export_sitemap.files)

        with mock.patch.object(pipelines, 'lxml'):
            with mock.patch.object(pipelines, 'open'):
                self.export_sitemap.spider_closed(self.spider)

        self.assertFalse(self.spider in self.export_sitemap.files)

    def test_spider_closed_parses_with_lxml(self):
        self.export_sitemap.exporter = mock.MagicMock()
        self.export_sitemap.exporter.finish_exporting = mock.MagicMock()
        self.export_sitemap.files[self.spider] = mock.MagicMock()

        with mock.patch.object(pipelines.lxml, 'etree'):
            with mock.patch.object(pipelines.lxml.etree,
                                   'parse') as mocked_lxml_parse:
                with mock.patch.object(pipelines, 'open'):
                    self.export_sitemap.spider_closed(self.spider)

        self.assertTrue(mocked_lxml_parse.called)

    def test_spider_closed_opens_xml_files(self):
        self.export_sitemap.exporter = mock.MagicMock()
        self.export_sitemap.exporter.finish_exporting = mock.MagicMock()
        self.export_sitemap.files[self.spider] = mock.MagicMock()

        with mock.patch.object(pipelines, 'lxml'):
            with mock.patch.object(pipelines, 'open') as mocked_open:
                self.export_sitemap.spider_closed(self.spider)

        self.assertTrue(mocked_open.called)

    def test_spider_closed_writes_tree(self):
        self.export_sitemap.exporter = mock.MagicMock()
        self.export_sitemap.exporter.finish_exporting = mock.MagicMock()
        self.export_sitemap.files[self.spider] = mock.MagicMock()

        with mock.patch.object(pipelines.lxml, 'etree'):
            with mock.patch.object(pipelines.lxml.etree,
                                   'tostring') as mocked_lxml_tostring:
                with mock.patch.object(pipelines, 'open'):
                    self.export_sitemap.spider_closed(self.spider)

        self.assertTrue(mocked_lxml_tostring.called)

    def test_process_item_exports_item(self):
        item = spider = self.export_sitemap.exporter = mock.MagicMock()
        self.export_sitemap.exporter.export_item = mock.MagicMock()
        self.export_sitemap.process_item(item, spider)

        self.assertTrue(self.export_sitemap.exporter.export_item.called)

    def test_process_item_returns_item(self):
        spider = self.export_sitemap.exporter = mock.MagicMock()
        item = {'random': 'item'}
        returned_item = self.export_sitemap.process_item(item, spider)

        self.assertEqual(item, returned_item)

    def test_from_crawler_exists(self):
        attr_exists = hasattr(pipelines.ExportSitemap, 'from_crawler')
        attr_callable = callable(getattr(pipelines.ExportSitemap,
                                         'from_crawler'))
        self.assertTrue(attr_exists and attr_callable)

    def test_from_crawler_assigns_pipeline(self):
        crawler = mock.MagicMock()
        pipelines.ExportSitemap.from_crawler(crawler)
        # still thinking how to go about here.

if __name__ == '__main__':
    unittest.main()
