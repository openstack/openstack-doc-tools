autogenerate_config_docs
========================

Automatically generate configuration tables to document OpenStack.


Dependencies: python-git (at least version 0.3.2 RC1), oslo-incubator,
openstack-doc-tools

Setting up your environment
---------------------------

Note: This tool is best run in a fresh VM environment or a python virtual
environment, as running it requires installing the dependencies of the
particular OpenStack product you are working with. Installing all of that on
your normal machine could leave you with a bunch of cruft!

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
conflicts happen with installed files (e.g. a change from `foo/bar.py`
to `foo/bar/__init__.py`). For best results, uninstall the old product
and install from git using setup.py.


Using the tool
--------------

This tool is divided into three parts:

1. Extraction of flags names:

        $ openstack-doc-tools/autogenerate_config_docs/autohelp.py create nova -i /repos/nova

    You only need to use the `create` action to add a new product.
    Otherwise, use `update`:

        $ openstack-doc-tools/autogenerate_config_docs/autohelp.py update nova -i /repos/nova

    The `create` action will create a new `nova.flagmappings` file,
    possibly overriding an existing file. The `update` action will
    create a `nova.flagmappings.new` file, merging in group
    information from the existing `nova.flagmappings` file.

2. Grouping of flags

   This is currently done manually, by using the flag name file and placing
   a category after a space:

        $ head nova.flagmappings
        aggregate\_image\_properties\_isolation\_namespace scheduling
        aggregate\_image\_properties\_isolation\_separator scheduling
        allow\_instance\_snapshots policy
        allow\_migrate\_to\_same\_host policy
        allow\_resize\_to\_same\_host policy
        allow\_same\_net\_traffic network
        allowed\_direct\_url\_schemes glance
        ...

3. Creation of docbook-formatted configuration table files:

   Example:

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

Update automatically generated tables - from scratch, using a virtual
environment. Using a python virtual environment will avoid modifications and
conflicts with python packages installed on the base system. The virtual
environment can be destroyed by deleting the `venv` directory.

Note that the virtual environment must be activated for every new shell you
start. This can be done by sourcing the `venv/bin/activate` file.

    $ mkdir WORKDIR
    $ cd WORKDIR
    $ sudo apt-get update
    $ sudo apt-get install git python-virtualenv
    $ virtualenv venv
    $ source venv/bin/activate
    $ git clone git://git.openstack.org/openstack/openstack-doc-tools.git
    $ git clone git://git.openstack.org/openstack/openstack-manuals.git
    $ git clone git://git.openstack.org/openstack/oslo-incubator
    $ cd oslo-incubator
    $ python setup.py install
    $ cd ..
    $ pip install "GitPython>=0.3.2.RC1"
    $ cd openstack-manuals/tools/autogenerate-config-flagmappings

Now, download and install the projects. Installation is necessary to satisfy
dependencies between projects. This will also install required dependencies.

    $ mkdir -p sources && cd sources
    $ PROJECTS="ceilometer cinder glance heat neutron nova trove"
    $ for p in $PROJECTS; do git clone git://git.openstack.org/openstack/$p.git; done
    $ for p in $PROJECTS; do cd $p && python setup.py install && cd ..; done
    $ cd ..

Install some missing requirements:

    $ pip install fixtures swift hp3parclient ryu pymongo bson

Note that some dependencies will still be missing. They can't be installed using
pip, they should be installed manually. Not installing those dependencies will
not prevent the tool to work, but some configuration options might not be
discovered.

Update the flag names:

    $ for p in $PROJECTS; do
    > ../../../openstack-doc-tools/autogenerate_config_docs/autohelp.py -vvv update $project
    > done

At this point, search through the `*.flagmappings.new` files for anything
labelled `Unknown` and fix it. Once that is done rename the `*.flagmappings.new`
files and run `autohelp.py` with the `docbook` subcommand:

    $ for p in $PROJECTS; do
    > mv $p.flagmappings.new $p.flagmappings
    > ../../../openstack-doc-tools/autogenerate_config_docs/autohelp.py -vvv docbook $project
    > done

to generate the XML files and move those into the appropriate part of
the git repo.
