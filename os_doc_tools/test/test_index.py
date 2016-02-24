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
from os_doc_tools import index
import unittest


class TestGenerateIndex(unittest.TestCase):
    def test_dir_created(self):
        path = 'path'
        with mock.patch.object(index, 'open'):
            with mock.patch.object(index.os, 'mkdir') as mock_mkdir:
                index.generate_index_file(path)
        self.assertTrue(mock_mkdir.called)

    def test_dir_not_created_when_exists(self):
        path = 'path'
        with mock.patch.object(index, 'open'):
            with mock.patch.object(index.os, 'mkdir') as mock_mkdir:
                with mock.patch.object(index.os.path, 'isdir',
                                       returned_value=True):
                    index.generate_index_file(path)
        self.assertFalse(mock_mkdir.called)


if __name__ == '__main__':
    unittest.main()
