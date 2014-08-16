#!/usr/bin/env bash

set -x

# This script downloads all dependencies to be able
# to build the documents.

for repository in $(ls -d -1 /home/vagrant/repositories/*); do
    cd $repository
    for document in $(find . -name pom.xml); do
        pushd ${document%/*};
        mvn clean generate-sources
        mvn clean
        popd
    done
done
