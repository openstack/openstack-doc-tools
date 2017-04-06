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
from os_doc_tools import jsoncheck
import unittest


class MockOpen(object):

    def read(self):
        return "raw"

    def write(self):
        return True


class TestFileFunctions(unittest.TestCase):

    def test_indent_note(self):
        note = "Hello\nWorld"
        with mock.patch.object(jsoncheck.textwrap, 'fill') as mock_fill:
            mock_fill.return_value = "Hello World"
            jsoncheck._indent_note(note)
            mock_fill.assert_any_call('Hello', initial_indent='    ',
                                      subsequent_indent='            ',
                                      width=80)
            mock_fill.assert_any_call('World', initial_indent='    ',
                                      subsequent_indent='            ',
                                      width=80)

    def test_get_demjson_diagnostics(self):
        raw = "raw"

        with mock.patch.object(jsoncheck.demjson, 'decode', return_value=True):
            errstr = jsoncheck._get_demjson_diagnostics(raw)
            self.assertTrue(errstr is None)

        with mock.patch.object(jsoncheck.demjson, 'decode') as mock_decode:
            mock_decode.side_effect = jsoncheck.demjson.JSONError(raw)
            errstr = jsoncheck._get_demjson_diagnostics(raw)
            expected_error_str = "     Error: raw"
            self.assertEqual(errstr, expected_error_str)

    def test_parse_json(self):
        raw = "raw"
        with mock.patch.object(jsoncheck.json, 'loads',
                               return_value="Success"):
            parsed = jsoncheck._parse_json(raw)
        self.assertEqual(parsed, "Success")

        with mock.patch.object(jsoncheck.json, 'loads') as mock_loads:
            mock_loads.side_effect = ValueError()
            with self.assertRaises(jsoncheck.ParserException):
                parsed = jsoncheck._parse_json(raw)

    def test_format_parsed_json(self):
        with mock.patch.object(jsoncheck.json, 'dumps') as mock_dumps:
            mock_dumps.return_value = "Success"
            returned_value = jsoncheck._format_parsed_json('raw')
        self.assertEqual(returned_value, "Success\n")
        self.assertTrue(mock_dumps.called)

    def test_process_file(self):
        with mock.patch.object(jsoncheck, 'open', returned_value=MockOpen()):
            with mock.patch.object(jsoncheck, '_parse_json') as mock_parse:
                mock_parse.side_effect = jsoncheck.ParserException
                with self.assertRaises(ValueError):
                    jsoncheck._process_file('path')

        with mock.patch.object(jsoncheck, 'open', returned_value=MockOpen()):
            with mock.patch.object(jsoncheck, '_parse_json',
                                   returned_value="Success"):
                with mock.patch.object(jsoncheck, '_format_parsed_json',
                                       returned_value="not_raw"):
                        with self.assertRaises(ValueError):
                            jsoncheck._process_file('path', 'check')

        with mock.patch.object(jsoncheck, 'open', returned_value=MockOpen()):
            with mock.patch.object(jsoncheck, '_parse_json',
                                   returned_value="Success"):
                with mock.patch.object(jsoncheck, '_format_parsed_json',
                                       returned_value="not_raw"):
                    with self.assertRaises(ValueError):
                        jsoncheck._process_file('path', 'formatting')


if __name__ == '__main__':
    unittest.main()
