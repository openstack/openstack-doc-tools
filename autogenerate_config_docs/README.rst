.. _autogenerate_config_docs:

autogenerate_config_docs
========================

Automatically generate configuration tables to document OpenStack.

Using the wrapper
-----------------

``autohelp-wrapper`` is the recommended tool to generate the configuration
tables. Don't bother using ``autohelp.py`` manually.

The ``autohelp-wrapper`` script installs a virtual environment and all the
needed dependencies, clones or updates the projects and manuals repositories,
then runs the ``autohelp.py`` script in the virtual environment.

New and updated flagmappings are generated in the ``openstack-manuals``
repository (``tools/autogenerate-config-flagmappings/`` directory).

Prior to running the following commands, you need to install several development
packages.

On Ubuntu:

.. code-block:: console

    $ sudo apt-get install python-dev python-pip python-virtualenv \
                           libxml2-dev libxslt1-dev zlib1g-dev \
                           libmysqlclient-dev libpq-dev libffi-dev \
                           libsqlite3-dev libldap2-dev libsasl2-dev \
                           libjpeg-dev

On RHEL 7 and CentOS 7:

.. code-block:: console

    $ sudo yum install https://www.rdoproject.org/repos/rdo-release.rpm
    $ sudo yum update
    $ sudo yum install python-devel python-pip python-virtualenv \
                           libxml2-devel libxslt-devel zlib-devel \
                           mariadb-devel postgresql-devel libffi-devel \
                           sqlite-devel openldap-devel cyrus-sasl-devel \
                           libjpeg-turbo-devel gcc git

.. note::
    * libjpeg is needed for ironic

The workflow is:

.. code-block:: console

    $ pip install -rrequirements.txt
    $ ./autohelp-wrapper update
    $ $EDITOR sources/openstack-manuals/tools/autogenerate-config-flagmappings/*.flagmappings
    $ ./autohelp-wrapper rst
    $ # check the results in sources/openstack-manuals

This will generate the tables for all the known projects.
Note for neutron project: If the driver/plugin resides outside the neutron
repository, then the driver/plugin has to be explicitly installed within the
virtual environment to generate the configuration options.

To generate the mappings and tables for a subset of projects, use the code
names as arguments:

.. code-block:: console

    $ ./autohelp-wrapper update cinder heat
    $ # edit the mappings files
    $ ./autohelp-wrapper rst cinder heat


Flagmappings files
------------------

The tool uses flagmapping files to map options to custom categories. Flag
mapping files can be found in the ``tools/autogenerate-config-flagmappings``
folder of the openstack-manuals project. Not all projects use flagmapping
files, as those that do not will be disabled by the presence of a
``$project.disable`` file in that folder. For those that do, however, the files
use the following format::

    OPTION_SECTION/OPTION_NAME group1 [group2, ...]

Groups need to be defined manually to organize the configuration tables.

The group values can only contain alphanumeric characters, _ and - (they will
be used as document IDs).

To make the table titles more user friendly, create or edit the PROJECT.headers
file in the manuals repository. Each line of this file is of the form:

::

    GROUP A Nice Title

Working with branches
---------------------

``autohelp-wrapper`` works on the master branch by default, but you can tell it
to work on another branch:

.. code-block:: console

    $ ./autohelp-wrapper -b stable/liberty update

.. note::
   The ``-b`` switch doesn't apply to the ``openstack-manuals`` repository
   which will be left untouched (no ``git branch``, no ``git update``).


Generate configuration difference
---------------------------------

To generate "New, updated, and deprecated options" for each service,
run ``diff_branches.py``. For example:

.. code-block:: console

   $ ./diff_branches.py stable/liberty stable/mitaka nova
