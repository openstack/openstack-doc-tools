#!/bin/bash -ex

# Documentation can be submitted in markdown and then converted to docbook
# so it can be built with the maven plugin. This is used by Jenkins when
# invoking certain docs jobs and the resulting output is made available to maven.

# In case we start doing something more sophisticated with other refs
# later (such as tags).
BRANCH=$ZUUL_REFNAME
shopt -s extglob

# Find location of db4-upgrade-xsl:
if [ -e /usr/share/xml/docbook/stylesheet/docbook5/db4-upgrade.xsl ] ; then
  DB_UPGRADE=/usr/share/xml/docbook/stylesheet/docbook5/db4-upgrade.xsl
elif [ -e  /usr/share/xml/docbook/stylesheet/upgrade/db4-upgrade.xsl ] ; then
  DB_UPGRADE=/usr/share/xml/docbook/stylesheet/upgrade/db4-upgrade.xsl
else
  echo "db4-upgrade.xsl not found"
  exit 1
fi

# Need to get the file name to insert here so it can be reused for multiple projects
# Filenames for the known repos that could do this are openstackapi-programming.mdown
# and images-api-v2.0.md and openstackapi-programming and images-api-v2.0 are the names
# for the ID and xml filename.
FILENAME=$1
FILEPATH=`find ./ -regextype posix-extended -regex ".*${FILENAME}\.(md|markdown|mdown)"`
DIRPATH=`dirname $FILEPATH`
SOURCES=`ls $DIRPATH/*.md`

# Check for requirements
type -P pandoc > /dev/null 2>&1 || { echo >&2 "pandoc not installed.  Aborting."; exit 1; }
type -P xsltproc > /dev/null 2>&1 || { echo >&2 "xsltproc not installed.  Aborting."; exit 1; }
type -P xmllint > /dev/null 2>&1 || { echo >&2 "xmllint not installed.  Aborting."; exit 1; }

pandoc -f markdown -t docbook -s ${SOURCES} |\
xsltproc -o - ${DB_UPGRADE} - |\
xmllint  --format - | \
sed -e "s,<article,<chapter xml:id=\"$FILENAME\"," | \
sed -e 's,</article>,</chapter>,' > ${DIRPATH}/$FILENAME.xml

pwd
