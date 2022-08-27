import json
import lupa.lua52
import re
from collections import defaultdict
from typing import Any, Match, Iterator, Callable, TypeVar, Generator, TYPE_CHECKING

from defines import defines
from mod_reader import ModReader
from utils import parse_dependencies, python_to_lua_table, lua_table_to_python
from factorio_types import ItemWithCount, Recipe, Tech, Item, Entity, SUPERCLASS, Group, Subgroup


R = TypeVar('R')


if not TYPE_CHECKING:
    FactorioData = None


class FactorioData:
    def __init__(self, base_dir: str, mod_cache_dir: str, mods: list[str],
                 username: str, token: str, quiet: bool = False):
        self.character = Entity(
                self, dict(name='character', type='character')
        )

        self.base_dir = base_dir
        self.reader = ModReader(base_dir, mod_cache_dir, username, token)
        self.quiet = quiet

        self.mod_list, self.mod_info = self._populate_mod_list(set(mods))
        self.mod_versions = {
                name: info.get('version', None)
                for name, info in self.mod_info.items()}
        self.locale = self._init_locale()
        self.raw = self._read_raw_data()

        self.items = {item.name: item
                      for item in (self._get_all_of_type('item', Item))}
        self.entities = {entity.name: entity
                         for entity in (self._get_all_of_type('entity', Entity))}
        self.recipes = {name: Recipe(self, value)
                        for name, value in self.raw['recipe'].items()}
        self.technologies = {name: Tech(self, value)
                             for name, value in self.raw['technology'].items()
                             if 'count' in self.raw['technology'][name]['unit']}

        self.groups = {name: Group(self, value)
                       for name, value in self.raw['item-group'].items()}
        self.subgroups = {name: Subgroup(self, value)
                          for name, value in self.raw['item-subgroup'].items()}

    def _read_raw_data(self) -> Any:
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

        lua = self._init_lua()
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

    def _init_lua(self) -> lupa.lua52.LuaRuntime:
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

        lua = lupa.lua52.LuaRuntime(unpack_returned_tuples=True)  # noqa (PyCharm doesn't like that argument)
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

    def _populate_mod_list(self, mods: set[str]) -> tuple[list[str], dict[str, Any]]:
        mods.update({'base', 'core'})

        # Get all mods including dependencies
        mod_info: dict[str, Any] = {}
        load_order_constraints: dict[str, list[str]] = {}
        while True:
            new_mods = mods - mod_info.keys()
            if len(new_mods) == 0:
                break

            for mod in new_mods:
                self.reader.add_mod(mod)
                mod_info[mod] = json.loads(self.reader.get_text(f'__{mod}__/info.json'))

                required_dependencies = []
                load_order_constraints[mod] = []
                for dependency_spec in mod_info[mod].get('dependencies', []):
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

        return mod_list, mod_info

    def _init_locale(self) -> dict[str, str]:
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

    def _get_all_of_type(
            self,
            base_class: str,
            constructor: Callable[[FactorioData, Any], R]) \
            -> Generator[R, None, None]:
        for subclass, superclass in SUPERCLASS.items():
            if superclass == base_class:
                yield from self._get_all_of_type(subclass, constructor)

        for raw_element in self.raw.get(base_class, {}).values():
            yield constructor(self, raw_element)

    def localize(self, name: str) -> str:
        def get_localized_from_group(match_object: Match[str]) -> str:
            if match_object[1] == 'ENTITY':
                return self.localize(f'entity-name.{match_object[2]}')
            elif match_object[1] == 'ITEM':
                return self.localize(f'item-name.{match_object[2]}')
            else:
                return match_object[0]

        if name in self.locale:
            localized = self.locale[name]
        else:
            match = re.match(r'(.*)-(\d+)$', name)
            if not match or match[1] not in self.locale:
                # XXX This is a horrible kludge
                return ''
            localized = self.locale[match[1]] + ' ' + match[2]

        localized = str(re.sub('__([^_]*)__([^_]*)__', get_localized_from_group, localized))
        # localized = str(re.sub('__plural_for_parameter_(\d*)_{(.*)}', get_plural, localized))
        return localized

    def localize_array(self, array: list[Any]) -> str:
        def localize_match(match: Match[str]) -> str:
            return self.localize_array(array[int(match[1])])

        if isinstance(array, str):
            return array
        elif isinstance(array, (int, float)):
            return str(array)
        elif not array[0]:
            return ''.join(self.localize_array(x) for x in array)
        else:
            return re.sub(r'__(\d+)__', localize_match, self.localize(array[0]))

    def get_crafting_machines_for(self, crafting_category: str) -> Iterator[tuple[Entity, float]]:
        crafting_machine_types = [
            "assembling-machine",
            "furnace",
            "rocket-silo"
        ]

        if crafting_category == 'crafting':
            yield self.character, 1

        for crafter_type in crafting_machine_types:
            for machine_name, machine in sorted(self.raw[crafter_type].items()):
                if crafting_category in machine['crafting_categories']:
                    name = machine_name

                    try:
                        yield self.entities[name], machine['crafting_speed']
                    except KeyError:
                        # TODO
                        pass
