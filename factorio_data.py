import configparser
import json
import lupa
import re
from collections import defaultdict

from defines import defines
from icon import get_factorio_icon, get_icon_specs
from mod_reader import ModReader
from property_tree import read_tree_file
from utils import python_to_lua_table, lua_table_to_python


class FactorioData:
    def __init__(self, base_dir, mods_dir, mods):
        self.base_dir = base_dir
        self.mods_dir = mods_dir
        self.reader = ModReader(base_dir, mods_dir)

        self.populate_mod_list(mods)
        self.init_locale()
        self.init_lua()

        self.lua.globals().mods = python_to_lua_table(self.lua, self.mod_versions)
        self.execute_file_from_mod('core', 'lualib/dataloader')
        for filename in ['settings', 'settings-updates', 'settings-final-fixes']:
            for mod in self.mod_list:
                self.execute_file_from_mod(mod, filename)
        self.raw = lua_table_to_python(self.lua.globals().data.raw)

        # Datatype: bool, int, etc.
        # Setting type: startup, runtime, etc.
        settings = defaultdict(dict)
        for setting_datatype in ['bool', 'int', 'double', 'string']:
            if f'{setting_datatype}-setting' in self.raw:
                for setting_name, data in self.raw[f'{setting_datatype}-setting'].items():
                    settings[data['setting_type']][setting_name] = {
                        'value': data['default_value']
                    }

        # TODO incorporate settings from JSON of from live mod-settings:
        # read_tree_file(f'{self.mods_dir}/mod-settings.dat')
        self.lua.globals().settings = settings

        for filename in ['data', 'data-updates', 'data-final-fixes']:
            for mod in self.mod_list:
                self.execute_file_from_mod(mod, filename)
        self.raw = lua_table_to_python(self.lua.globals().data.raw)

    def init_lua(self):
        def lua_package_searcher(require_argument):
            # Lua allows "require foo.bar.baz", "require foo/bar/baz" and "require
            # foo/bar/baz.lua". Convert the former two to the latter, canonical form.
            if not '/' in require_argument:
                require_argument = require_argument.replace('.', '/')
            if not require_argument.endswith('.lua'):
                require_argument += '.lua'

            # Paths starting '__modname__' are absolute. Paths that don't should be
            # treated relative to either the current module or the root directory of
            # the current game mod.
            if require_argument.startswith('__'):
                paths = [require_argument]
            else:
                # The global dir_stack table has the name of the current module's
                # directory in position 1, always with a trailing slash.
                if not self.lua.globals().dir_stack:
                    return
                current_module = self.lua.globals().dir_stack[1]
                game_mod_root = re.match('(__.*__/).*', current_module)[1]
                paths = [current_module + require_argument, game_mod_root + require_argument]

            for path in paths:
                path_elements = path.split('/')
                new_dir_stack_entry = '/'.join(path_elements[0:-1]) + '/'

                try:
                    contents = self.reader.get_text(path)
                except FileNotFoundError:
                    continue

                return self.lua.eval('''
                    (function(new_dir_stack_entry, contents, filename)
                        return function ()
                            table.insert(dir_stack, 1, new_dir_stack_entry)
                            ret = load(contents, filename)()
                            table.remove(dir_stack, 1)
                            return ret
                        end
                    end)(...)''',
                    new_dir_stack_entry,
                    contents,
                    path)

        self.lua = lupa.LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('serpent = require("serpent")')
        self.lua.globals().package.path = \
                f'{self.base_dir}/base/?.lua;{self.base_dir}/core/lualib/?.lua'
        self.lua.globals().defines = python_to_lua_table(self.lua, defines)
        self.lua.execute('table.insert(package.searchers, 1, ...)', lua_package_searcher)
        self.lua.globals().log = self.log
        self.lua.execute('''
            function math.pow(a, b)
                return a ^ b
            end

            require "util"

            function table_size(t)
                local count = 0
                for k,v in pairs(t) do
                    count = count + 1
                end
                return count
            end
        ''')

    def execute_file_from_mod(self, mod, filename):
        try:
            text = self.reader.get_text(f'__{mod}__/{filename}.lua')
        except FileNotFoundError:
            return

        # Reset package.loaded in between every module because some modules use
        # packages with identical names.
        self.lua.execute(f'''
            dir_stack = {{"__{mod}__/"}}
            for k, v in pairs(package.loaded) do
                package.loaded[k] = false
            end
        ''')
        self.lua.execute(text)

    def log(self, value):
        print(lua_table_to_python(value))

    def populate_mod_list(self, mods):
        mods = set(mods)
        mods.update({'base', 'core'})

        # Get all mods including dependencies
        self.mod_versions = {}
        load_order_constraints = {}
        while True:
            new_mods = mods - self.mod_versions.keys()
            if len(new_mods) == 0:
                break

            for mod in new_mods:
                info_json = json.loads(self.reader.get_text(f'__{mod}__/info.json'))
                self.mod_versions[mod] = info_json.get('version', None)
                # ! for incompatibility
                # ? for an optional dependency
                # (?) for a hidden optional dependency
                # ~ for a dependency that does not affect load order
                # or no prefix for a hard requirement for the other mod.

                # Get all required dependencies, and also all optional
                # dependencies that affect load order
                required_deps = []
                load_order_constraints[mod] = []
                for dependency_spec in info_json['dependencies']:
                    if dependency_spec[0] not in "!(?)~":
                        dependency_spec = '= ' + dependency_spec
                    prefix, dep = dependency_spec.split(' ')[0:2]
                    if prefix in {'=', '~'}:
                        required_deps.append(dep)
                    if prefix in {'=', '?', '(?)'}:
                        load_order_constraints[mod].append(dep)

                mods.update(required_deps)

        # Now order them
        self.mod_list = ['core', 'base']
        while True:
            new_mods = {
                    mod
                    for mod in mods
                    if set(load_order_constraints[mod]).intersection(mods).issubset(self.mod_list)}
            new_mods -= set(self.mod_list)
            if len(new_mods) == 0:
                break
            self.mod_list.extend(new_mods)

    def init_locale(self):
        self.locale = configparser.ConfigParser()
        for mod in self.mod_list:
            for localefile in self.reader.glob(f'__{mod}__/locale/en/*.cfg'):
                self.locale.read_string('[EMPTYSECTION]\n' + self.reader.get_text(localefile))

    def get_item_icon(self, item_name):
        item_types = [
                'ammo',
                'armor',
                'blueprint',
                'blueprint-book',
                'capsule',
                'copy-paste-tool',
                'deconstruction-item',
                'gun',
                'item',
                'item-with-entity-data',
                'item-with-inventory',
                'item-with-label',
                'item-with-tags',
                'module',
                'rail-planner',
                'repair-tool',
                'selection-tool',
                'spidertron-remote',
                'tool',
                'upgrade-item',
                ]
        for item_type in item_types:
            if item_name in self.raw[item_type]:
                return get_factorio_icon(self.reader, get_icon_specs(self.raw[item_type][item_name]))

    def get_tech_icon(self, tech_name):
        return get_factorio_icon(self.reader, get_icon_specs(self.raw['technology'][tech_name]))

    def get_recipe_icon(self, recipe_name):
        recipe = self.raw['recipe'][recipe_name]
        try:
            spec = get_icon_specs(recipe)
        except KeyError:
            main_item_name = recipe.get('main_product', recipe['results'][0]['name'])
            item = self.raw['item'][main_item_name]
            spec = get_icon_specs(item)

        return get_factorio_icon(self.reader, spec)

    def localize(self, section, value):
        def get_localized_from_group(match):
            if match[1] == 'ENTITY':
                return self.localize('entity-name', match[2])
            elif match[1] == 'ITEM':
                return self.localize('item-name', match[2])
            else:
                return match[0]

        if value in self.locale[section]:
            localized = self.locale[section][value]
        else:
            match = re.match('(.*)-(\d+)$', value)
            if match:
                localized = self.locale[section].get(match[1], '???') + ' ' + match[2]
            else:
                localized = '???'
        return re.sub('__([^_]*)__([^_]*)__', get_localized_from_group, localized)
