==================
openstack-doc-test
==================

------------------------------------------------------
OpenStack Validation tool
------------------------------------------------------

SYNOPSIS
========

openstack-doc-test [options]

DESCRIPTION
===========

openstack-doc-test allows to test the validity of the OpenStack documentation content.

OPTIONS
=======

  **General options**

  **--api-site**
       Special handling for api-site and other API repositories
       to handle WADL.

  **--check-build**
        Try to build books using modified files.

  **--check-syntax**
        Check the syntax of modified files.

  **--check-deletions**
       Check that deleted files are not used.

  **--check-niceness**
       Check the niceness of files, for example whitespace.

  **--check-all**
       Run all checks (default if no arguments are given).

  **--config-file PATH**
       Path to a config file to use. Multiple config files can be
       specified, with values in later files taking precedence.

  **--file-exception FILE_EXCEPTION**
      File that will be skipped during validation.

  **--force**
        Force the validation of all files and build all books.

  **-h, --help**
        Show help message and exit.

  **--ignore-dir IGNORE_DIR**
      Directory to ignore for building of manuals. The parameter can
      be passed multiple times to add several directories.

  **--ignore-errors**
       Do not exit on failures.

  **--verbose**
       Verbose execution.

  **--version**
       Output version number.

FILES
=====

Reads the file `doc-test.conf` in the top-level directory of the git
repository for option processing.

SEE ALSO
========

* `OpenStack Documentation <http://wiki.openstack.org/wiki/Documentation>`__

Bugs
====

* openstack-doc-tools is hosted on Launchpad so you can view current
  bugs at
  `Bugs : openstack-manuals <https://bugs.launchpad.net/openstack-manuals/>`__
