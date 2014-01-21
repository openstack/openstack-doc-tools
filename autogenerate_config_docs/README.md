autogenerate_config_docs
========================

Automatically generate configuration tables to document OpenStack.


Dependencies: python-git (at least version 0.3.2 RC1), oslo.config,
	      oslo-incubator, openstack-doc-tools

Setting up your environment
---------------------------

Note: This tool is best run in a fresh VM environment, as running it
 requires installing the dependencies of the particular OpenStack
 product you are working with. Installing all of that on your normal
machine could leave you with a bunch of cruft!

Install git and python-pip:

    $ sudo apt-get install git python-pip

Install oslo.config and GitPython:

    $ sudo pip install oslo.config "GitPython>=0.3.2.RC1"

Install oslo-incubator from git:

    $ git clone git://git.openstack.org/openstack/oslo-incubator
    $ cd oslo-incubator
    $ python setup.py build
    $ sudo python setup.py install

Check out the repository you are working with:

    $ git clone https://git.openstack.org/openstack/nova.git

(This guide makes reference to a /repos directory, so you should
record the directory you are using and replace as appropriate below.)

Check out the tool itself:

    $ git clone https://git.openstack.org/openstack/openstack-doc-tools.git

Install the dependencies for the product you are working with:

    $ sudo pip install -r nova/requirements.txt

Note 1: Occasionally, the requirements.txt file does not reference all
dependencies needed to import all modules in a package. You may need
to manually install some dependencies with pip or your distro's
package manager. Always check the log for failed imports.

Note 2: Although this tool imports from your checkout, occasionally
conflicts happen with installed files (e.g. a change from foo/bar.py
to foo/bar/__init__.py). For best results, uninstall the old product
and install from git using setup.py.


Using the tool
--------------

This tool is divided into three parts:

1) Extraction of flags names

    $ openstack-doc-tools/autogenerate_config_docs/autohelp.py create nova -i /repos/nova

You only need to use the `create` action to add a new product.
Otherwise, use `update`.

    $ openstack-doc-tools/autogenerate_config_docs/autohelp.py update nova -i /repos/nova

The `create` action will create a new `nova.flagmappings` file,
possibly overriding an existing file. The `update` action will
create a `nova.flagmappings.new` file, merging in group information
from the existing `nova.flagmappings` file.

2) Grouping of flags

This is currently done manually, by using the flag name file and placing
a category after a space.

    $ head nova.flagmappings
    aggregate\_image\_properties\_isolation\_namespace scheduling
    aggregate\_image\_properties\_isolation\_separator scheduling
    allow\_instance\_snapshots policy
    allow\_migrate\_to\_same\_host policy
    allow\_resize\_to\_same\_host policy
    allow\_same\_net\_traffic network
    allowed\_direct\_url\_schemes glance
    ...

3) Creation of docbook-formatted configuration table files

    $ openstack-doc-tools/autogenerate_config_docs/autohelp.py docbook nova -i /repos/nova


Duplicate options
-----------------

Sometimes the log will tell you there was a duplicate option name.
This often happens if a parent module does `import *` from a child
module. For example, `nova.db` does `from nova.db.api import *`.
If one module name is a child of the other, the tool will use the
option from the more specific module and tell you so. This is
probably not a problem.

If the tool tells you it's chosing one at random, then something
else is happening, and you should investigate. Otherwise, you may
lose an option.


A worked example - updating the docs for Icehouse
-------------------------------------------------
update automatically generated tables - from scratch

 $ sudo apt-get update
 $ sudo apt-get install git python-pip python-dev
 $ sudo pip install git-review GitPython
 $ git clone git://git.openstack.org/openstack/openstack-manuals.git
 $ git clone git://git.openstack.org/openstack/openstack-doc-tools.git
 $ cd openstack-manuals/
 $ git review -d 35726
 $ cd tools/autogenerate-config-flagmappings

Now, cloning and installing requirements for nova, glance, quantum

 $ for i in nova glance neutron; do git clone git://git.openstack.org/openstack/$i.git; done
 $ for i in nova glance neutron; do sudo pip install -r $i/requirements.txt; done

This missed some requirements for nova, which were fixed by:

 $ sudo pip install python-glanceclient websockify pyasn1 python-cinderclient error\_util
 $ sudo apt-get install python-ldap python-lxml

Making the flag names update

 $ ../../openstack-doc-tools/autogenerate_config_docs/autohelp.py -vvv update nova -i ~/nova > nova.log

At this point, search through nova.flagmappings.new for anything
labelled Unknown and fix, once that is done use:

 $ ../../openstack-doc-tools/autogenerate_config_docs/autohelp.py -vvv docbook nova -i ~/nova

to generate the XML files and move those into the appropriate part of
the git repo
