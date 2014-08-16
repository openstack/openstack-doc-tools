#!/usr/bin/env bash

# Just a helper script to package a running Vagrant environment.

if [[ -z $1 ]]; then
    echo "usage: $0 VERSION"
    exit 1
fi

version=$1
rm -f working.tar.bz2
touch working/.placeholder
tar cjf working.tar.bz2 working
vagrant package \
    --output=openstack-manuals-$version.box \
    --vagrantfile=Vagrantfile.box \
    --include working.tar.bz2
