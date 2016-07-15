#!/usr/bin/env python

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

import argparse
import os
import sys


def generate_index_file(publish_path):
    """Generate index.html file in publish_path."""

    if not os.path.isdir(publish_path):
        os.mkdir(publish_path)

    index_file = open(os.path.join(publish_path, 'index.html'), 'w')

    index_file.write(
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n'
        '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        '<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">\n'
        '<body>\n'
        '<h1>Generated documents</h1>\n')

    links = {}
    for root, dirs, files in os.walk(publish_path):

        dirs[:] = [d for d in dirs if d not in ['common', 'webapp', 'content',
                                                'www', 'samples']]

        # Ignore top-level index.html files
        if root == publish_path:
            continue

        if os.path.isfile(os.path.join(root, 'content/index.html')):
            path = os.path.relpath(root, publish_path)
            links[path] = ('<a href="%s/content/index.html">%s</a>\n' %
                           (path, path))
        elif os.path.isfile(os.path.join(root, 'index.html')):
            path = os.path.relpath(root, publish_path)
            links[path] = ('<a href="%s/index.html">%s</a>\n' %
                           (path, path.replace('draft/', '')))

        if os.path.isfile(os.path.join(root, 'api-ref.html')):
            path = os.path.relpath(root, publish_path)
            links[path] = ('<a href="%s/api-ref.html">%s</a>\n' %
                           (path, path))

        # List PDF files for api-site that have from "bk-api-ref*.pdf"
        # as well since they have no corresponding html file.
        for f in files:
            if f.startswith('bk-api-ref') and f.endswith('.pdf'):
                path = os.path.relpath(root, publish_path)
                links[f] = ('<a href="%s/%s">%s</a>\n' %
                            (path, f, f))

    for entry in sorted([s for s in links if not s.startswith('draft/')]):
        index_file.write(links[entry])
        index_file.write('<br/>\n')

    drafts = [s for s in links if s.startswith('draft/')]
    if drafts:
        index_file.write('<h2>Draft guides</h2>\n')
    for entry in sorted(drafts):
        index_file.write(links[entry])
        index_file.write('<br/>\n')

    if os.path.isfile(os.path.join(publish_path, 'www-index.html')):
        index_file.write('<h2>WWW index pages</h2>\n')
        index_file.write('<a href="www-index.html">List of generated '
                         'WWW pages</a>\n')
    index_file.write('</body>\n'
                     '</html>\n')
    index_file.close()


def main():
    parser = argparse.ArgumentParser(description="Generate index file.")
    parser.add_argument('directory', metavar='DIR',
                        help="Directory to search.")
    args = parser.parse_args()

    generate_index_file(args.directory)

if __name__ == "__main__":
    sys.exit(main())
