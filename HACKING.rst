openstack-doc-tools style commandments
======================================

- Step 1: Read the OpenStack Style Commandments
  http://docs.openstack.org/developer/hacking/

- Step 2: Read on

Running tests
-------------

So far there are no tests included with the package but a test suite
would be welcome!

Since the openstack-doc-test tool is used for gating of the OpenStack
documentation repositories, test building of these repositories with
any changes done here.

Testing can be done with simply a local install of
openstack-doc-tools, then checking out the gated repositories and
running: ``tox`` inside of each.

The repositories gated by openstack-doc-tools are:
* api-guide
* openstack-manuals
* operations-guide
