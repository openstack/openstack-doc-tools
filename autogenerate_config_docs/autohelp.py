#!/usr/bin/env python
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
# A collection of tools for working with flags from OpenStack
# packages and documentation.
#
# For an example of usage, run this program with the -h switch.
#

# Must import this before argparse
from oslo_config import cfg

import argparse
import importlib
import os
import pickle
import re
import sys

import jinja2
import stevedore

try:
    from sqlalchemy import exc
except Exception:
    pass

sys.path.insert(0, '.')
from hooks import HOOKS  # noqa


EXTENSIONS = ['oslo.cache',
              'oslo.concurrency',
              'oslo.db',
              'oslo.log',
              'oslo.messaging',
              'oslo.middleware',
              'oslo.policy',
              'oslo.service']

_TYPE_DESCRIPTIONS = {
    cfg.StrOpt: 'String',
    cfg.BoolOpt: 'Boolean',
    cfg.IntOpt: 'Integer',
    cfg.FloatOpt: 'Floating point',
    cfg.ListOpt: 'List',
    cfg.DictOpt: 'Dict',
    cfg.PortOpt: 'Port number',
    cfg.MultiStrOpt: 'Multi-valued',
    cfg._ConfigFileOpt: 'List of filenames',
    cfg._ConfigDirOpt: 'List of directory names',
}

register_re = re.compile(r'''^ +.*\.register_opts\((?P<opts>[^,)]+)'''
                         r'''(, (group=)?["'](?P<group>.*)["'])?\)''')


def import_modules(repo_location, package_name, verbose=0):
    """Import modules.

    Loops through the repository, importing module by module to
    populate the configuration object (cfg.CONF) created from Oslo.
    """

    with open('ignore.list') as fd:
        ignore_list = [l for l in fd.read().split('\n')
                       if l and (l[0] != '#')]

    pkg_location = os.path.join(repo_location, package_name)
    for root, dirs, files in os.walk(pkg_location):
        skipdir = False
        for excludedir in ('tests', 'locale',
                           os.path.join('db', 'migration'), 'transfer'):
            if ((os.path.sep + excludedir + os.path.sep) in root or (
                    root.endswith(os.path.sep + excludedir))):
                skipdir = True
                break
        if skipdir:
            continue
        for pyfile in files:
            if pyfile.endswith('.py'):
                abs_path = os.path.join(root, pyfile)
                modfile = abs_path.split(repo_location, 1)[1]
                modname = os.path.splitext(modfile)[0].split(os.path.sep)
                modname = [m for m in modname if m != '']
                modname = '.'.join(modname)
                if modname.endswith('.__init__'):
                    modname = modname[:modname.rfind(".")]
                if modname in ignore_list:
                    continue
                try:
                    module = importlib.import_module(modname)
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
                except cfg.DuplicateOptError as e:
                    """
                    oslo.cfg doesn't allow redefinition of a config option, but
                    we don't mind. Don't fail if this happens.
                    """
                    if verbose >= 2:
                        print(e)
                    continue
                except cfg.NoSuchGroupError as e:
                    """
                    If a group doesn't exist, we ignore the import.
                    """
                    if verbose >= 2:
                        print(e)
                    continue
                except exc.InvalidRequestError as e:
                    if verbose >= 2:
                        print(e)
                    continue
                except Exception as e:
                    print("Impossible to import module %s" % modname)
                    raise e

                _register_runtime_opts(module, abs_path, verbose)
                _run_hook(modname)

    # All the components provide keystone token authentication, usually using a
    # pipeline. Since the auth_token options can only be discovered at runtime
    # in this configuration, we force their discovery by importing the module.
    try:
        import keystonemiddleware.auth_token  # noqa
    except cfg.DuplicateOptError:
        pass


def _run_hook(modname):
    try:
        HOOKS[modname]()
    except KeyError:
        pass


def _register_runtime_opts(module, abs_path, verbose):
    """Handle options not registered on module import.

    This function parses the .py files to discover calls to register_opts in
    functions and methods. It then explicitly call cfg.register_opt on each
    option to register (most of) them.
    """

    with open(abs_path) as fd:
        for line in fd:
            m = register_re.search(line)
            if not m:
                continue

            opts_var = m.group('opts')
            opts_group = m.group('group')

            # Get the object (an options list) from the opts_var string.
            # This requires parsing the string which can be of the form
            # 'foo.bar'. We treat each element as an attribute of the previous.
            register = True
            obj = module
            for item in opts_var.split('.'):
                try:
                    obj = getattr(obj, item)
                except AttributeError:
                    # FIXME(gpocentek): AttributeError is raised when a part of
                    # the opts_var string is not an actual attribute. This will
                    # need more parsing tricks.
                    register = False
                    if verbose >= 2:
                        print("Ignoring %(obj)s in %(module)s" %
                              {'obj': opts_var, 'module': module})
                    break

            if register:
                for opt in obj:
                    if not isinstance(opt, cfg.Opt):
                        continue
                    try:
                        cfg.CONF.register_opt(opt, opts_group)
                    except cfg.DuplicateOptError:
                        # ignore options that have already been registered
                        pass


def _sanitize_default(opt):
    """Adapts unrealistic default values."""

    # If the Oslo version is recent enough, we can use the 'sample_default'
    # attribute
    if (hasattr(opt, 'sample_default') and opt.sample_default is not None):
        return str(opt.sample_default)

    if ((type(opt).__name__ == "ListOpt") and (type(opt.default) == list)):
        return ", ".join(opt.default)

    default = str(opt.default)

    if default == os.uname()[1]:
        return 'localhost'

    if opt.name == 'bindir':
        return '/usr/local/bin'

    if opt.name == 'my_ip':
        return '10.0.0.1'

    if isinstance(opt, cfg.StrOpt) and default.strip() != default:
        return '"%s"' % default

    for pathelm in sys.path:
        if pathelm in ('.', ''):
            continue
        if pathelm.endswith('/'):
            pathelm = pathelm[:-1]
        if pathelm in default:
            default = re.sub(r'%s(/sources)?' % pathelm,
                             '/usr/lib/python/site-packages', default)

    return default


def _get_overrides(package_name):
    overrides_file = '%s.overrides' % package_name
    if not os.path.exists(overrides_file):
        return {}
    overrides = {}
    with open(overrides_file) as fd:
        for line in fd:
            if line == '#':
                continue
            try:
                opt, sections = line.strip().split(' ', 1)
                sections = [x.strip() for x in sections.split(' ')]
            except ValueError:
                continue

            overrides[opt] = sections

    return overrides


class OptionsCache(object):
    def __init__(self, overrides={}, verbose=0):
        self._verbose = verbose
        self._opts_by_name = {}
        self._opt_names = []
        self._overrides = overrides

        for optname in cfg.CONF._opts:
            opt = cfg.CONF._opts[optname]['opt']
            # We ignore some CLI opts by excluding SubCommandOpt objects
            if not isinstance(opt, cfg.SubCommandOpt):
                self._add_opt(optname, 'DEFAULT', opt)

        for group in cfg.CONF._groups:
            for optname in cfg.CONF._groups[group]._opts:
                self._add_opt(group + '/' + optname, group,
                              cfg.CONF._groups[group]._opts[optname]['opt'])

        self._opt_names.sort(OptionsCache._cmpopts)

    def _add_opt(self, optname, group, opt):
        if optname in self._opts_by_name:
            if self._verbose >= 2:
                print ("Duplicate option name %s" % optname)
            return

        opt.default = _sanitize_default(opt)

        def fill(optname, group, opt):
            if optname in self._opts_by_name:
                return
            self._opts_by_name[optname] = (group, opt)
            self._opt_names.append(optname)

        if optname in self._overrides:
            for new_group in self._overrides[optname]:
                if new_group == 'DEFAULT':
                    new_optname = opt.name
                else:
                    new_optname = new_group + '/' + opt.name
                fill(new_optname, new_group, opt)

        else:
            fill(optname, group, opt)

    def __len__(self):
        return len(self._opt_names)

    def load_extension_options(self, module):
        # Note that options loaded this way aren't added to _opts_by_module
        loader = stevedore.named.NamedExtensionManager(
            'oslo.config.opts',
            names=(module,),
            invoke_on_load=False
        )
        for ext in loader:
            for group, opts in ext.plugin():
                for opt in opts:
                    if group is None:
                        self._add_opt(opt.dest, 'DEFAULT', opt)
                    else:
                        self._add_opt(group + '/' + opt.dest, group, opt)

        self._opt_names.sort(OptionsCache._cmpopts)

    def maybe_load_extensions(self, repositories):
        # Use the requirements.txt of the project to guess if an oslo module
        # needs to be imported
        needed_exts = set()
        for repo in repositories:
            base_path = os.path.dirname(repo)
            for ext in EXTENSIONS:
                requirements = os.path.join(base_path, 'requirements.txt')
                with open(requirements) as fd:
                    for line in fd:
                        if line.startswith(ext):
                            needed_exts.add(ext)

        for ext in needed_exts:
            self.load_extension_options(ext)

    def get_option_names(self):
        return self._opt_names

    def get_option(self, name):
        return self._opts_by_name[name]

    def dump(self):
        """Dumps the list of options with their attributes.

        This output is consumed by the diff_branches script.
        """
        for name, (group, option) in self._opts_by_name.items():
            deprecated_opts = [{'group': deprecated.group,
                                'name': deprecated.name}
                               for deprecated in option.deprecated_opts]
            help_str = option.help.strip() if option.help else "None"
            new_option = {
                'default': option.default,
                'help': help_str,
                'deprecated_opts': deprecated_opts,
                'type': option.__class__.__name__.split('.')[-1]
            }
            self._opts_by_name[name] = (group, new_option)
        print(pickle.dumps(self._opts_by_name))

    @staticmethod
    def _cmpopts(x, y):
        if '/' in x and '/' in y:
            prex = x[:x.find('/')]
            prey = y[:y.find('/')]
            if prex != prey:
                return cmp(prex, prey)
            return cmp(x, y)
        elif '/' in x:
            return 1
        elif '/' in y:
            return -1
        else:
            return cmp(x, y)


def pass_through(line):
    """Whether to ignore the line."""
    return (not line.strip() or
            line.startswith('#'))


def _get_options_by_cat(package_name):
    options_by_cat = {}

    with open(package_name + '.flagmappings') as f:
        for line in f:
            if pass_through(line):
                continue
            opt, categories = line.split(' ', 1)
            for category in categories.split():
                options_by_cat.setdefault(category, []).append(opt)

    return options_by_cat


def _get_category_names(package_name):
    package_headers = package_name + '.headers'
    category_names = {}
    for headers_file in ('shared.headers', package_headers):
        try:
            with open(headers_file) as f:
                for line in f:
                    if pass_through(line):
                        continue
                    cat, nice_name = line.split(' ', 1)
                    category_names[cat] = nice_name.strip()
        except IOError:
            print("Cannot open %s (ignored)" % headers_file)

    return category_names


def write_files(package_name, options, target, output_format):
    """Write tables.

    Prints a table for every group of options.
    """
    if not target:
        if output_format == 'rst':
            target = '../../doc/config-reference/source/tables'
        else:
            target = '../../doc/common/tables/'
    options_by_cat = _get_options_by_cat(package_name)
    category_names = _get_category_names(package_name)

    if not os.path.isdir(target):
        os.makedirs(target)

    for cat in options_by_cat.keys():
        env = {
            'pkg': package_name,
            'cat': cat,
            'groups': [],
            'items': [],
        }

        # Skip the options that is explicitly marked as disabled,
        # which is used for common configuration options.
        if cat == 'disable':
            continue

        if cat in category_names:
            env['nice_cat'] = category_names[cat]
        else:
            env['nice_cat'] = cat
            print("No nicename for %s" % cat)

        curgroup = None
        items = None
        for optname in options_by_cat[cat]:
            group, option = options.get_option(optname)

            if group != curgroup:
                if group is not None:
                    curgroup = group
                    env['groups'].append(group)
                    if items is not None:
                        env['items'].append(items)
                items = []

            if not option.help:
                option.help = "No help text available for this option."

            helptext = option.help.strip()
            helptext = helptext.replace('\n\n', '$sentinal$')
            helptext = helptext.replace('\n*', '$sentinal$*')
            helptext = helptext.replace('\n', ' ')
            helptext = ' '.join(helptext.split())
            # TODO(johngarbutt) space matches only the current template :(
            helptext = helptext.replace('$sentinal$', '\n\n       ')

            if option.deprecated_for_removal:
                if not option.help.strip().startswith('DEPRECATED'):
                    helptext = 'DEPRECATED: ' + helptext
                if getattr(option, 'deprecated_reason', None):
                    helptext += ' ' + option.deprecated_reason

            opt_type = _TYPE_DESCRIPTIONS.get(type(option), 'Unknown')
            flags = []
            if option.mutable:
                flags.append(('Mutable', 'This option can be changed without'
                              ' restarting.'))
            item = (option.dest,
                    _sanitize_default(option),
                    "(%s) %s" % (opt_type, helptext),
                    flags)
            items.append(item)

        env['items'].append(items)
        env['table_label'] = package_name + '-' + cat

        ext = 'rst' if output_format == 'rst' else 'xml'
        file_path = ("%(target)s/%(package_name)s-%(cat)s.%(ext)s" %
                     {'target': target, 'package_name': package_name,
                      'cat': cat, 'ext': ext})
        tmpl_file = os.path.join(os.path.dirname(__file__),
                                 'templates/autohelp.%s.j2' % output_format)
        with open(tmpl_file) as fd:
            template = jinja2.Template(fd.read(), trim_blocks=True)
            output = template.render(filename=file_path, **env)

        with open(file_path, 'w') as fd:
            fd.write(output)


def update_flagmappings(package_name, options, verbose=0):
    """Update flagmappings file.

    Update a flagmappings file, adding or removing entries as needed.
    This will create a new file $package_name.flagmappings.new with
    category information merged from the existing $package_name.flagmappings.
    """
    original_flags = {}
    try:
        with open(package_name + '.flagmappings') as f:
            for line in f:
                try:
                    flag, category = line.split(' ', 1)
                except ValueError:
                    flag = line.strip()
                    category = "Unknown"
                original_flags.setdefault(flag, []).append(category.strip())
    except IOError:
        # If the flags file doesn't exist we'll create it
        pass

    updated_flags = []
    for opt in options.get_option_names():
        if len(original_flags.get(opt, [])) == 1:
            updated_flags.append((opt, original_flags[opt][0]))
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


def main():
    parser = argparse.ArgumentParser(
        description='Manage flag files, to aid in updating documentation.',
        usage='%(prog)s <cmd> <package> [options]')
    parser.add_argument('subcommand',
                        help='Action (update, docbook, rst, dump).',
                        choices=['update', 'docbook', 'rst', 'dump'])
    parser.add_argument('package',
                        help='Name of the top-level package.')
    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        dest='verbose',
                        required=False,)
    parser.add_argument('-i', '--input',
                        dest='repos',
                        help='Path to a python package in which options '
                             'should be discoverd. Can be used multiple '
                             'times.',
                        required=False,
                        type=str,
                        action='append')
    parser.add_argument('-o', '--output',
                        dest='target',
                        help='Directory or file in which data will be saved.\n'
                             'Defaults to ../../doc/common/tables/ '
                             'for "docbook".\n'
                             'Defaults to stdout for "dump"',
                        required=False,
                        type=str,)
    args = parser.parse_args()

    if args.repos is None:
        args.repos = ['./sources/%s/%s' % args.package]

    for repository in args.repos:
        package_name = os.path.basename(repository)
        base_path = os.path.dirname(repository)

        sys.path.insert(0, base_path)
        try:
            __import__(package_name)
        except ImportError as e:
            if args.verbose >= 1:
                print(str(e))
                print("Failed to import: %s (%s)" % (package_name, e))

        import_modules(base_path, package_name, verbose=args.verbose)
        sys.path.pop(0)

    overrides = _get_overrides(package_name)
    options = OptionsCache(overrides, verbose=args.verbose)
    options.maybe_load_extensions(args.repos)

    if args.verbose > 0:
        print("%s options imported from package %s." % (len(options),
                                                        str(package_name)))

    if args.subcommand == 'update':
        update_flagmappings(args.package, options, verbose=args.verbose)

    elif args.subcommand in ('docbook', 'rst'):
        write_files(args.package, options, args.target, args.subcommand)

    elif args.subcommand == 'dump':
        options.dump()


if __name__ == "__main__":
    main()
