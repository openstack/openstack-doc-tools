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
from sitemap.generator import items
import unittest


class TestSitemapItem(unittest.TestCase):

    def test_class_type(self):
        self.assertTrue(type(items.SitemapItem) is items.scrapy.item.ItemMeta)

    def test_class_supports_fields(self):
        with mock.patch.object(items.scrapy.item, 'Field'):
            a = items.SitemapItem()

        supported_fields = ['loc', 'lastmod', 'priority', 'changefreq']
        for field in supported_fields:
            a[field] = field

        not_supported_fields = ['some', 'random', 'fields']
        for field in not_supported_fields:
            with self.assertRaises(KeyError):
                a[field] = field

if __name__ == '__main__':
    unittest.main()
