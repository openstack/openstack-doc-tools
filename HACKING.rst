openstack-doc-tools style commandments
======================================

- Step 1: Read the OpenStack Style Commandments
  http://docs.openstack.org/developer/hacking/

- Step 2: Read on

Running tests
-------------

So far there are no tests included with the package but a test suite
would be welcome!

The openstack-indexpage tool is used while building the OpenStack
documentation repositories, test building of these repositories with
any changes done here.

Testing can be done with simply a local install of
openstack-doc-tools, then checking out the repositories and
running: ``tox`` inside of each.

The repositories using openstack-doc-tools include:
* api-site
* openstack-manuals
* security-doc
