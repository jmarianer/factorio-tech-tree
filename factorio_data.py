import json
import lupa
import re
from collections import defaultdict
from typing import Any, Match, Iterator

from defines import defines
from mod_reader import ModReader
from utils import parse_dependencies, python_to_lua_table, lua_table_to_python
from factorio_types import ItemWithCount, Recipe, Tech, Item


class FactorioData:
    def __init__(self, base_dir: str, mod_cache_dir: str, mods: list[str],
                 username: str, token: str, quiet: bool = False):
        self.base_dir = base_dir
        self.reader = ModReader(base_dir, mod_cache_dir, username, token)
        self.quiet = quiet

        self.mod_list, self.mod_versions = self.populate_mod_list(set(mods))
        self.locale = self.init_locale()
        self.raw = self.read_raw_data()

    def read_raw_data(self) -> Any:
        def maybe_execute(path: str) -> Any:
            try:
                text = self.reader.get_text(path)
            except FileNotFoundError:
                return

            # Reset package.loaded in between every module because some modules use
            # packages with identical names.
            mod_root = path.split('/')[0] + '/'
            lua.eval(
                '''
                (function(new_dir_stack_entry, contents, filename)
                    dir_stack = {new_dir_stack_entry}
                    for k, v in pairs(package.loaded) do
                        package.loaded[k] = false
                    end
                    load(contents, filename)()
                end)(...)''',
                mod_root,
                text,
                path)

        lua = self.init_lua()
        lua.globals().mods = python_to_lua_table(lua, self.mod_versions)
        maybe_execute('__core__/lualib/dataloader.lua')
        for filename in ['settings', 'settings-updates', 'settings-final-fixes']:
            for mod in self.mod_list:
                maybe_execute(f'__{mod}__/{filename}.lua')
        raw_settings = lua_table_to_python(lua.globals().data.raw)

        # Datatype: bool, int, etc.
        # Setting type: startup, runtime, etc.
        settings: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(lambda: None))
        for setting_datatype in ['bool', 'int', 'double', 'string']:
            if f'{setting_datatype}-setting' in raw_settings:
                for setting_name, data in raw_settings[f'{setting_datatype}-setting'].items():
                    settings[data['setting_type']][setting_name] = {
                        'value': data['default_value']
                    }

        # TODO incorporate settings from JSON of from live mod-settings:
        # read_tree_file('.../mod-settings.dat')
        lua.globals().settings = settings

        for filename in ['data', 'data-updates', 'data-final-fixes']:
            for mod in self.mod_list:
                maybe_execute(f'__{mod}__/{filename}.lua')
        return lua_table_to_python(lua.globals().data.raw)

    def init_lua(self) -> lupa.LuaRuntime:
        def lua_package_searcher(require_argument: str) -> Any:
            # Lua allows "require foo.bar.baz", "require foo/bar/baz" and "require
            # foo/bar/baz.lua". Convert the former two to the latter, canonical form.
            if '/' not in require_argument:
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
                if not lua.globals().dir_stack:
                    return
                current_module = lua.globals().dir_stack[1]
                match = re.match('(__.*__/).*', current_module)
                if match:
                    game_mod_root = match[1]
                else:
                    raise
                paths = [current_module + require_argument, game_mod_root + require_argument]

            for path in paths:
                path_elements = path.split('/')
                new_dir_stack_entry = '/'.join(path_elements[0:-1]) + '/'

                try:
                    contents = self.reader.get_text(path)
                except FileNotFoundError:
                    continue

                return lua.eval(
                    '''
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

        lua = lupa.LuaRuntime(unpack_returned_tuples=True)  # noqa (PyCharm doesn't like that argument)
        lua.execute('serpent = require("serpent")')
        lua.globals().package.path = \
            f'{self.base_dir}/base/?.lua;{self.base_dir}/core/lualib/?.lua'
        lua.globals().defines = python_to_lua_table(lua, defines)
        lua.execute('table.insert(package.searchers, 1, ...)', lua_package_searcher)
        lua.globals().log = self.log
        lua.execute('''
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

        return lua

    def log(self, value: str) -> None:
        if not self.quiet:
            print(lua_table_to_python(value))

    def populate_mod_list(self, mods: set[str]) -> tuple[list[str], dict[str, str]]:
        mods.update({'base', 'core'})

        # Get all mods including dependencies
        mod_versions: dict[str, str] = {}
        load_order_constraints: dict[str, list[str]] = {}
        while True:
            new_mods = mods - mod_versions.keys()
            if len(new_mods) == 0:
                break

            for mod in new_mods:
                self.reader.add_mod(mod)
                info_json = json.loads(self.reader.get_text(f'__{mod}__/info.json'))
                mod_versions[mod] = info_json.get('version', None)

                required_dependencies = []
                load_order_constraints[mod] = []
                for dependency_spec in info_json.get('dependencies', []):
                    prefix, dep, _ = parse_dependencies(dependency_spec)
                    if prefix in {None, '~'}:
                        required_dependencies.append(dep)
                    if prefix in {None, '?', '(?)'}:
                        load_order_constraints[mod].append(dep)

                mods.update(required_dependencies)

        # Now order them
        mod_list = ['core', 'base']
        while True:
            new_mods = {
                    mod
                    for mod in mods
                    if set(load_order_constraints[mod]).intersection(mods).issubset(mod_list)}
            new_mods -= set(mod_list)
            if len(new_mods) == 0:
                break
            mod_list.extend(new_mods)

        return mod_list, mod_versions

    def init_locale(self) -> dict[str, str]:
        locale: dict[str, str] = {}
        for mod in self.mod_list:
            prefix = ''
            for locale_file in self.reader.glob(f'__{mod}__/locale/en/*.cfg'):
                for line in self.reader.get_text(locale_file).splitlines():
                    if not line or line[0] in ';#':
                        continue
                    if line.startswith('['):
                        prefix = line[1:-1] + '.'
                        continue
                    name, value = line.split('=', 1)
                    locale[prefix + name] = value

        return locale

    # TODO: Consider creating all of these in advance and just grabbing them from a dict
    def get_item(self, item_name: str) -> Item:
        item_types = [
            'item',
            'item-with-entity-data',
            'item-with-inventory',
            'item-with-label',
            'item-with-tags',
            'active-defense-equipment',
            'ammo',
            'armor',
            'assembling-machine',
            'blueprint',
            'blueprint-book',
            'boiler',
            'capsule',
            'copy-paste-tool',
            'deconstruction-item',
            'equipment',
            'fluid',
            'gun',
            'mining-tool',
            'module',
            'rail-planner',
            'repair-tool',
            'selection-tool',
            'spidertron-remote',
            'storage-tank',
            'tool',
            'upgrade-item',
        ]

        # TODO is this even remotely correct?
        raw_item = {}
        for item_type in reversed(item_types):
            if item_type in self.raw and item_name in self.raw[item_type]:
                raw_item.update(self.raw[item_type][item_name])
        return Item(self, raw_item, item_name, item_type)

    def raw_to_item_list(self, raw_items: list[Any]) -> Iterator[ItemWithCount]:
        for raw_item in raw_items:
            if isinstance(raw_item, dict):
                name = raw_item['name']
                if 'amount' in raw_item:
                    amount = raw_item['amount']
                else:
                    amount = f'{raw_item["amount_min"]}–{raw_item["amount_max"]}'
            else:
                name, amount = raw_item
            yield ItemWithCount(self, name, amount)

    def get_recipe(self, recipe_name: str) -> Recipe:
        raw_recipe = self.raw['recipe'][recipe_name]

        if 'normal' in raw_recipe:
            raw_recipe = raw_recipe['normal']

        if 'results' in raw_recipe:
            results = raw_recipe['results']
        else:
            results = [[raw_recipe['result'], 1]]
        return Recipe(
            self,
            raw_recipe,
            name=recipe_name,
            ingredients=list(self.raw_to_item_list(raw_recipe['ingredients'])),
            products=list(self.raw_to_item_list(results)),
            time=raw_recipe.get('energy_required', 0.5),
        )

    def get_tech(self, tech_name: str) -> Tech:
        raw_tech = self.raw['technology'][tech_name]
        count = raw_tech['unit']['count']
        ingredients = [
            ItemWithCount(self, i.name, i.amount * count)
            for i in self.raw_to_item_list(raw_tech['unit']['ingredients'])]
        return Tech(
            self,
            raw_tech,
            name=raw_tech['name'],
            time=raw_tech['unit']['time'] * count,
            prerequisite_names=set(raw_tech.get('prerequisites', [])),
            ingredients=ingredients,
            recipes=[self.get_recipe(effect['recipe'])
                     for effect in raw_tech.get('effects', [])
                     if 'recipe' in effect])

    def localize(self, name: str) -> str:
        def get_localized_from_group(match_object: Match[str]) -> str:
            if match_object[1] == 'ENTITY':
                return self.localize(f'entity-name.{match_object[2]}')
            elif match_object[1] == 'ITEM':
                return self.get_item(match_object[2]).localized_title
            else:
                return match_object[0]

        if name in self.locale:
            localized = self.locale[name]
        else:
            match = re.match(r'(.*)-(\d+)$', name)
            if not match:
                raise
            localized = self.locale[match[1]] + ' ' + match[2]

        return str(re.sub('__([^_]*)__([^_]*)__', get_localized_from_group, localized))

    def localize_array(self, array: list[Any]) -> str:
        def localize_match(match: Match[str]) -> str:
            new_value = array[int(match[1])]

            if isinstance(new_value, str):
                return new_value
            return self.localize_array(new_value)

        return re.sub(r'__(\d+)__', localize_match, self.localize(array[0]))
