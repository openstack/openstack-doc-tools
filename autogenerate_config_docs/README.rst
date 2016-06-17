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

Prior to running the following commands you need to install several development
packages. For Ubuntu install the required packages with the following command:

.. code-block:: console

    $ sudo apt-get install python-dev python-pip python-virtualenv \
                           libxml2-dev libxslt1-dev zlib1g-dev \
                           libmysqlclient-dev libpq-dev libffi-dev \
                           libsqlite3-dev libldap2-dev libsasl2-dev \
                           libjpeg-dev liberasurecode-dev


.. note::
    * libjpeg is needed for ironic
    * liberasurecode-dev is needed for swift

The workflow is:

.. code-block:: console

    $ pip install -rrequirements.txt
    $ ./autohelp-wrapper update
    $ $EDITOR sources/openstack-manuals/tools/autogenerate-config-flagmappings/*.flagmappings
    $ ./autohelp-wrapper rst
    $ # check the results in sources/openstack-manuals

This will generate the tables for all the known projects.
Note for Neutron project: If the driver/plugin resides outside the Neutron
repository in stackforge, then the driver/plugin has to be explicitly
installed within the virtual environment to generate the configuration
options.

To generate the mappings and tables for a subset of projects, use the code
names as arguments:

.. code-block:: console

    $ ./autohelp-wrapper update cinder heat
    $ # edit the mappings files
    $ ./autohelp-wrapper rst cinder heat


Flagmappings files
------------------

The flagmappings files use the following format:

::

    OPTION_SECTION/OPTION_NAME group1 [group2, ...]

Groups need to be defined manually to organize the configuration tables.

The group values can only contain alphanumeric characters, _ and - (they will
be used as docbook IDs).

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


Updating swift options
----------------------

Swift configuration tables are generated using the ``extract_swift_flags.py``
script. This script doesn't use a mapping file, but organize the tables using
the various configuration files and sections. Most of the options must be
described manually at the moment.

Generate configuration difference
---------------------------------

To generate "New, updated, and deprecated options" for each service,
run diff_branches.py. For example:

.. code-block:: console

   $ ./diff_branches.py stable/liberty stable/mitaka nova
