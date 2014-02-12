#
# A collection of shared functions for managing help flag mapping files.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

import importlib
import os
import sys

import git
import xml.sax.saxutils

import openstack.common.config.generator as generator


# gettext internationalisation function requisite:
import __builtin__
__builtin__.__dict__['_'] = lambda x: x


def git_check(repo_path):
    """Check a passed directory to verify it is a valid git repository."""

    try:
        repo = git.Repo(repo_path)
        assert repo.bare is False
        package_name = os.path.basename(repo.remotes.origin.url).rstrip('.git')
    except Exception:
        print("\nThere is a problem verifying that the directory passed in")
        print("is a valid git repository.  Please try again.\n")
        sys.exit(1)
    return package_name


def import_modules(repo_location, package_name, verbose=0):
    """Import modules.

    Loops through the repository, importing module by module to
    populate the configuration object (cfg.CONF) created from Oslo.
    """
    modules = {}
    pkg_location = os.path.join(repo_location, package_name)
    for root, dirs, files in os.walk(pkg_location):
        skipdir = False
        for excludedir in ('tests', 'locale', 'cmd',
                           os.path.join('db', 'migration'), 'transfer'):
            if ((os.path.sep + excludedir + os.path.sep) in root or (
                    root.endswith(os.path.sep + excludedir))):
                skipdir = True
                break
        if skipdir:
            continue
        for pyfile in files:
            if pyfile.endswith('.py'):
                modfile = os.path.join(root, pyfile).split(repo_location)[1]
                modname = os.path.splitext(modfile)[0].split(os.path.sep)
                modname = [m for m in modname if m != '']
                modname = '.'.join(modname)
                if modname.endswith('.__init__'):
                    modname = modname[:modname.rfind(".")]
                try:
                    module = importlib.import_module(modname)
                    modules[modname] = module
                    if verbose >= 1:
                        print("imported %s" % modname)
                except ImportError as e:
                    """
                    work around modules that don't like being imported in
                    this way FIXME This could probably be better, but does
                    not affect the configuration options found at this stage
                    """
                    if verbose >= 2:
                        print("Failed to import: %s (%s)" % (modname, e))
                    continue
    return modules


class OptionsCache(object):
    def __init__(self, modules, verbose=0):
        self._opts_by_module = {}
        self._opts_by_name = {}
        self._opt_names = []

        for modname in modules.keys():
            modopts = generator._list_opts(modules[modname])
            if len(modopts) == 0:
                continue
            self._opts_by_module[modname] = []
            for group, opts in modopts:
                for opt in opts:
                    self._opts_by_module[modname].append((group, opt))
                    if group == 'DEFAULT':
                        optname = opt.name
                    else:
                        optname = group + '/' + opt.name
                    if optname in self._opts_by_name:
                        oldmod = self._opts_by_name[optname][0]
                        if oldmod.startswith(modname + '.'):
                            if verbose >= 2:
                                print(("Duplicate option name %s" +
                                       " from %s and %s. Using %s.") %
                                      (optname, modname, oldmod, oldmod))
                        elif modname.startswith(oldmod + '.'):
                            self._opts_by_name[optname] = (modname, group, opt)
                            if verbose >= 2:
                                print (("Duplicate option name %s"
                                        " from %s and %s. Using %s.") %
                                       (optname, modname, oldmod, modname))
                        elif verbose >= 2:
                            print (("Duplicate option name %s"
                                    " from %s and %s. Taking one at random.") %
                                   (optname, modname, oldmod))
                    else:
                        self._opts_by_name[optname] = (modname, group, opt)
                        self._opt_names.append(optname)

        self._opt_names.sort(OptionsCache._cmpopts)

    def __len__(self):
        return len(self._opt_names)

    def get_option_names(self):
        return self._opt_names

    def get_option(self, name):
        return self._opts_by_name[name]

    @staticmethod
    def _cmpopts(x, y):
        if '/' in x and '/' in y:
            prex = x[:x.find('/')]
            prey = y[:x.find('/')]
            if prex != prey:
                return cmp(prex, prey)
            return cmp(x, y)
        elif '/' in x:
            return 1
        elif '/' in y:
            return -1
        else:
            return cmp(x, y)


def write_docbook(package_name, options, verbose=0):
    """Write DocBook tables.

    Prints a docbook-formatted table for every group of options.
    """
    options_by_cat = {}
    with open(package_name + '.flagmappings') as f:
        for line in f:
            opt, categories = line.split(' ', 1)
            for category in categories.split():
                options_by_cat.setdefault(category, []).append(opt)

    for cat in options_by_cat.keys():
        groups_file = open(package_name + '-' + cat + '.xml', 'w')
        groups_file.write('<?xml version="1.0" encoding="UTF-8"?>\n\
        <!-- Warning: Do not edit this file. It is automatically\n\
             generated and your changes will be overwritten.\n\
             The tool to do so lives in the tools directory of this\n\
             repository -->\n\
        <para xmlns="http://docbook.org/ns/docbook" version="5.0">\n\
        <table rules="all">\n\
          <caption>Description of configuration options for ' + cat +
                          '</caption>\n\
           <col width="50%"/>\n\
           <col width="50%"/>\n\
           <thead>\n\
              <tr>\n\
                  <th>Configuration option = Default value</th>\n\
                  <th>Description</th>\n\
              </tr>\n\
          </thead>\n\
          <tbody>\n')
        curgroup = None
        for optname in options_by_cat[cat]:
            modname, group, option = options.get_option(optname)
            if group != curgroup:
                curgroup = group
                groups_file.write('              <tr>\n')
                groups_file.write('                  ' +
                                  '<th colspan="2">[%s]</th>\n' %
                                  group)
                groups_file.write('              </tr>\n')
            if not option.help:
                option.help = "No help text available for this option"
            if ((type(option).__name__ == "ListOpt") and (
                    option.default is not None)):
                option.default = ", ".join(option.default)
            groups_file.write('              <tr>\n')
            default = generator._sanitize_default(option.name,
                                                  str(option.default))
            # This should be moved to generator._sanitize_default
            for pathelm in sys.path:
                if pathelm == '':
                    continue
                if pathelm.endswith('/'):
                    pathelm = pathelm[:-1]
                if default.startswith(pathelm):
                    default = default.replace(pathelm,
                                              '/usr/lib/python/site-packages')
                    break
            groups_file.write('                       <td>%s = %s</td>\n' %
                              (option.name, default))
            groups_file.write('                       <td>(%s) %s</td>\n' %
                              (type(option).__name__,
                               xml.sax.saxutils.escape(option.help)))
            groups_file.write('              </tr>\n')
        groups_file.write('       </tbody>\n\
        </table>\n\
        </para>\n')
        groups_file.close()


def create_flagmappings(package_name, options, verbose=0):
    """Create a flagmappings file.

    Create a flagmappings file. This will create a new file called
    $package_name.flagmappings with all the categories set to Unknown.
    """
    with open(package_name + '.flagmappings', 'w') as f:
        for opt in options.get_option_names():
            f.write(opt + ' Unknown\n')


def update_flagmappings(package_name, options, verbose=0):
    """Update flagmappings file.

    Update a flagmappings file, adding or removing entries as needed.
    This will create a new file $package_name.flagmappings.new with
    category information merged from the existing $package_name.flagmappings.
    """
    original_flags = {}
    with open(package_name + '.flagmappings') as f:
        for line in f:
            flag, category = line.split(' ', 1)
            original_flags.setdefault(flag, []).append(category.strip())

    updated_flags = []
    for opt in options.get_option_names():
        if len(original_flags.get(opt, [])) == 1:
            updated_flags.append((opt, original_flags[opt][0]))
            continue

        if '/' in opt:
            # Compaitibility hack for old-style flagmappings, where grouped
            # options didn't have their group names prefixed. If there's only
            # one category, we assume there wasn't a conflict, and use it.
            barename = opt[opt.find('/') + 1:]
            if len(original_flags.get(barename, [])) == 1:
                updated_flags.append((opt, original_flags[barename][0]))
                continue

        updated_flags.append((opt, 'Unknown'))

    with open(package_name + '.flagmappings.new', 'w') as f:
        for flag, category in updated_flags:
            f.write(flag + ' ' + category + '\n')

    if verbose >= 1:
        removed_flags = (set(original_flags.keys()) -
                         set([x[0] for x in updated_flags]))
        added_flags = (set([x[0] for x in updated_flags]) -
                       set(original_flags.keys()))

        print("\nRemoved Flags\n")
        for line in sorted(removed_flags, OptionsCache._cmpopts):
            print(line)

        print("\nAdded Flags\n")
        for line in sorted(added_flags, OptionsCache._cmpopts):
            print(line)
