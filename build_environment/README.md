# Virtual build and testing environment

This is a virtual building and testing environment for the
OpenStack manuals using Vagrant to simplify the work.

## Getting started with Vagrant

* download a Vagrant package from http://www.vagrantup.com/downloads.html
* install and configure Vagrant like described
  at http://docs.vagrantup.com/v2/installation/index.html

## Build your own environment

To manually build your own environment you have to follow the following
steps.

Ansible (http://www.ansible.com/home) needs to be installed on the
workstation.

```
$ git clone https://github.com/openstack/openstack-doc-tools
$ cd openstack-doc-tools/build_environment
$ vagrant up
```

After ```vagrant up``` successfully finished you can login with
```vagrant ssh```. The virtual system can be destroyed with
```vagrant destroy```.

## Use the Vagrantbox from the VagrantCloud

Using the prebuilt box for VirtualBox on the VagrantCloud saves
a lot of time and you don't need to install Ansbile. Simply
follow the following steps:

```
$ vagrant box add openstack/openstack-manuals
$ mkdir /path/to/your/vagrantbox
$ cd /path/to/your/vagrantbox
$ vagrant init openstack/openstack-manuals
$ vagrant up
```

## Usage

To test and build the documents login into the box. The generated
files are browsable at http://localhost:8080/.

```
$ vagrant ssh
```

Go into the repositories located in ```/home/vagrant/repositories```
and build the documents with ```mvn clean generate-sources```.

To edit the documents and to commit changes you can use the toolchain
on the workstation. All repositories can be found in the local
directory ```repositories```. This directory is available inside the
virtual system at ```/home/vagrant/repositories```.

## Included repositories

* api-site
* compute-api
* docs-specs
* ha-guide
* identity-api
* image-api
* netconn-api
* object-api
* openstack-doc-tools
* openstack-manuals
* operations-guide
* security-doc
* training-guides
* volume-api

## Caveats

* At the moment the only tested provider is VirtualBox.
