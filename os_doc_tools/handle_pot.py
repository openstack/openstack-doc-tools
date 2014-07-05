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

'''
Created on 2012-7-3

@author: daisy
'''

import codecs
import optparse
import os
import shutil
import sys
import tempfile
import xml.dom.minidom

from xml2po import Main    # noqa
from xml2po.modes.docbook import docbookXmlMode    # noqa


class myDocbookXmlMode(docbookXmlMode):
    def __init__(self):
        self.lists = ['itemizedlist', 'orderedlist', 'variablelist',
                      'segmentedlist', 'simplelist', 'calloutlist',
                      'varlistentry', 'userinput', 'computeroutput',
                      'prompt', 'command', 'screen']
        self.objects = ['figure', 'textobject', 'imageobject', 'mediaobject',
                        'screenshot', 'literallayout', 'programlisting']

default_mode = 'docbook'
operation = 'merge'
xml_options = {
    'mark_untranslated': False,
    'expand_entities': True,
    'expand_all_entities': False,
}

IGNORE_FOLDER = []
IGNORE_FILE = []


def mergeback(folder, language, root):
    """Generate translated files for language in directory folder."""

    if folder is None:
        path = root
    else:
        outputFiles = mergeSingleDocument(folder, language, root)
        if (outputFiles is not None) and (len(outputFiles) > 0):
            for outXML in outputFiles:
                changeXMLLangSetting(outXML, language)
        return

    if not os.path.isdir(path):
        return

    files = os.listdir(path)
    for aFile in files:
        if not (aFile in IGNORE_FOLDER):
            outputFiles = mergeSingleDocument(aFile, language, root)
            if (outputFiles is not None) and (len(outputFiles) > 0):
                for outXML in outputFiles:
                    changeXMLLangSetting(outXML, language)


def mergeSingleDocument(folder, language, root):
    xmlfiles = []
    outputfiles = []
    abspath = os.path.join(root, folder)
    if os.path.isdir(abspath):
        os.path.walk(abspath, get_xml_list, xmlfiles)
    else:
        return None

    if len(xmlfiles) > 0:
        popath = os.path.join(abspath, "locale", language + ".po")
        # generate MO file
        mofile_handler, mofile_tmppath = tempfile.mkstemp()
        os.close(mofile_handler)
        os.system("msgfmt -o %s %s" % (mofile_tmppath, popath))

        for aXML in xmlfiles:
            # (filename, ext) = os.path.splitext(os.path.basename(aXML))
            relpath = os.path.relpath(aXML, root)
            outputpath = os.path.join(os.path.curdir, "generated", language,
                                      relpath)
            try:
                xml2po_main = Main(default_mode, "merge", outputpath,
                                   xml_options)
                xml2po_main.current_mode = myDocbookXmlMode()
                xml2po_main.merge(mofile_tmppath, aXML)
                outputfiles.append(outputpath)
            except IOError:
                print("Error: cannot open aFile %s for writing.")
                sys.exit(5)
            except Exception:
                print("Exception happen")
        if mofile_tmppath:
            os.remove(mofile_tmppath)

    return outputfiles


def changeXMLLangSetting(xmlFile, language):
    """Update XML settings for file."""

    # The mergeback breaks the ENTITIY title which should look like:
    # <!DOCTYPE chapter [
    # <!ENTITY % openstack SYSTEM "../common/entities/openstack.ent">
    # %openstack;
    # ]>
    # The "%openstack;" gets removed, let's add it back first.

    # NOTE(jaegerandi): This just handles the openstack ENTITY, if
    # others are used, this needs to be generalized.
    with open(xmlFile) as xml_file:
        newxml = xml_file.read()

    # Used in openstack-manuals:
    newxml = newxml.replace(
        'common/entities/openstack.ent">',
        'common/entities/openstack.ent"> %openstack;')

    # As used in security-doc and operations-guide
    newxml = newxml.replace('SYSTEM "openstack.ent">',
                            'SYSTEM "openstack.ent"> %openstack;')

    try:
        dom = xml.dom.minidom.parseString(newxml)
    except xml.parsers.expat.ExpatError as e:
        print("Error: parsing of file '%s' for language '%s' "
              "with Expat failed: %s." % (xmlFile, language, e))
        sys.exit(5)

    root = dom.documentElement
    root.setAttribute("xml:lang", language[:2])
    fileObj = codecs.open(xmlFile, "wb", encoding="utf-8")

    nodelists = root.getElementsByTagName("link")
    for node in nodelists:
        if node.hasAttribute("href"):
            node.setAttribute("xlink:href", node.getAttribute("href"))
        if node.hasAttribute("title"):
            node.setAttribute("xlink:title", node.getAttribute("title"))
    dom.writexml(fileObj)


def get_xml_list(sms, dr, flst):
    if (flst == "target") or (flst == "wadls"):
        return
    if dr.find("target") > -1:
        return
    if dr.find("wadls") > -1:
        return

    for f in flst:
        if (f.endswith(".xml") and (f != "pom.xml") and
           not (f in IGNORE_FILE)):
            sms.append(os.path.join(dr, f))


def get_default_book(root):
    return os.listdir(root)[0]


def generatedocbook():
    global IGNORE_FOLDER, IGNORE_FILE

    usage = "usage: %prog [options] command [cmd_options]"
    description = "This is the tool to generate translated docbooks, which "
    "will be stored in 'generated/[language]/"

    IGNORE_FOLDER = ["docbkx-example"]
    IGNORE_FILE = []

    parser = optparse.OptionParser(
        usage=usage, version="0.6", description=description
    )
    parser.disable_interspersed_args()
    parser.add_option(
        "-l", "--language", dest="language", help=("specified language")
    )
    parser.add_option(
        "-b", "--book", dest="book",
        help=("specified docbook")
    )
    parser.add_option(
        "-r", "--root", dest="root", default="./doc",
        help=("root directory")
    )
    (options, args) = parser.parse_args()
    if options.language is None:
        print("must specify language")
        return

    root = options.root
    if options.book is None:
        options.book = get_default_book(root)

    # change working directory

    # copy folders
    folder = options.book
    language = options.language
    root = options.root
    sourcepath = os.path.join(root, folder)
    destpath = os.path.join(os.path.curdir, "generated", language)
    if not os.path.exists(destpath):
        os.makedirs(destpath)

    destfolder = os.path.join(destpath, folder)
    if os.path.exists(destfolder):
        shutil.rmtree(destfolder)

    os.system("cp -r %s %s" % (sourcepath, destpath))
    mergeback(folder, language, root)


def generatePoT(folder, root):
    if folder is None:
        path = root
    else:
        generateSinglePoT(folder, root)
        return

    if not os.path.isdir(path):
        return

    files = os.listdir(path)
    for aFile in files:
        if not (aFile in IGNORE_FOLDER):
            generateSinglePoT(aFile, root)


def generateSinglePoT(folder, root):
    xmlfiles = []
    abspath = os.path.join(root, folder)
    if os.path.isdir(abspath):
        os.path.walk(abspath, get_xml_list, xmlfiles)
    else:
        return

    if len(xmlfiles) > 0:
        output = os.path.join(abspath, "locale")
        if not os.path.exists(output):
            os.mkdir(output)
        output = os.path.join(output, folder + ".pot")
        try:
            xml2po_main = Main(default_mode, "pot", output, xml_options)
            xml2po_main.current_mode = myDocbookXmlMode()
        except IOError:
            print("Error: cannot open aFile %s for writing." % (output))
            sys.exit(5)
        # print(xmlfiles)
        # print(">>>outout: %s ", output)
        xml2po_main.to_pot(xmlfiles)


def generatepot():
    global IGNORE_FOLDER, IGNORE_FILE

    IGNORE_FOLDER = ["docbkx-example", "training-guide"]
    IGNORE_FILE = ["api-examples.xml"]
    try:
        folder = sys.argv[1]
    except Exception:
        folder = None
    try:
        root = sys.argv[2]
    except Exception:
        root = "./doc"
    generatePoT(folder, root)
