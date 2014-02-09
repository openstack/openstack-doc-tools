#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from xml2po import Main
from xml2po.modes.docbook import docbookXmlMode


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
options = {
    'mark_untranslated': False,
    'expand_entities': True,
    'expand_all_entities': False,
}

IGNORE_FOLDER = []
IGNORE_FILE = []
root = "./doc"


def mergeback(folder, language):
    if folder is None:
        path = root
    else:
        outputFiles = mergeSingleDocument(folder, language)
        if (outputFiles is not None) and (len(outputFiles) > 0):
            for outXML in outputFiles:
                changeXMLLangSetting(outXML, language)
        return

    if not os.path.isdir(path):
        return

    files = os.listdir(path)
    for aFile in files:
        if not (aFile in IGNORE_FOLDER):
            outputFiles = mergeSingleDocument(aFile, language)
            if (outputFiles is not None) and (len(outputFiles) > 0):
                for outXML in outputFiles:
                    changeXMLLangSetting(outXML, language)


def mergeSingleDocument(folder, language):
    xmlfiles = []
    outputfiles = []
    abspath = os.path.join(root, folder)
    if os.path.isdir(abspath):
        os.path.walk(abspath, get_xml_list, xmlfiles)
    else:
        return None

    if len(xmlfiles) > 0:
        popath = os.path.join(abspath, "locale", language + ".po")
        #generate MO file
        mofile_handler, mofile_tmppath = tempfile.mkstemp()
        os.close(mofile_handler)
        os.system("msgfmt -o %s %s" % (mofile_tmppath, popath))

        for aXML in xmlfiles:
            #(filename, ext) = os.path.splitext(os.path.basename(aXML))
            relpath = os.path.relpath(aXML, root)
            outputpath = os.path.join(os.path.curdir, "generated", language,
                                      relpath)
            try:
                xml2po_main = Main(default_mode, "merge", outputpath,
                                   options)
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
    dom = xml.dom.minidom.parse(xmlFile)
    root = dom.documentElement
    root.setAttribute("xml:lang", language[:2])
    fileObj = codecs.open(xmlFile, "wb", encoding="utf-8")

    #add namespace to link
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


def get_default_book():
    return os.listdir(root)[0]


def generatedocbook():
    global IGNORE_FOLDER, IGNORE_FILE

    usage = "usage: %prog [options] command [cmd_options]"
    description = "This is the tool to generate translated docbooks, which"
    " will be stored in 'generated/[language]/"

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
        "-b", "--book", dest="book", default=get_default_book(),
        help=("specified docbook")
    )
    (options, args) = parser.parse_args()
    if options.language is None:
        print("must specify language")
        return

    #change working directory

    #copy folders
    folder = options.book
    language = options.language
    sourcepath = os.path.join(root, folder)
    destpath = os.path.join(os.path.curdir, "generated", language)
    if not os.path.exists(destpath):
        os.makedirs(destpath)

    destfolder = os.path.join(destpath, folder)
    if os.path.exists(destfolder):
        shutil.rmtree(destfolder)

    os.system("cp -r %s %s" % (sourcepath, destpath))
    mergeback(folder, language)


def generatePoT(folder):
    if folder is None:
        path = root
    else:
        generateSinglePoT(folder)
        return

    if not os.path.isdir(path):
        return

    files = os.listdir(path)
    for aFile in files:
        if not (aFile in IGNORE_FOLDER):
            generateSinglePoT(aFile)


def generateSinglePoT(folder):
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
            xml2po_main = Main(default_mode, "pot", output, options)
            xml2po_main.current_mode = myDocbookXmlMode()
        except IOError:
            print("Error: cannot open aFile %s for writing." % (output))
            sys.exit(5)
        #print(xmlfiles)
        #print(">>>outout: %s ", output)
        xml2po_main.to_pot(xmlfiles)


def generatepot():
    global IGNORE_FOLDER, IGNORE_FILE

    IGNORE_FOLDER = ["docbkx-example", "training-guide"]
    IGNORE_FILE = ["api-examples.xml"]
    try:
        folder = sys.argv[1]
    except Exception:
        folder = None
    generatePoT(folder)
