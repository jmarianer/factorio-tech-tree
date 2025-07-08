import json
import lupa.lua52
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from mod_reader import ModReader
from utils import parse_dependencies, python_to_lua_table, lua_table_to_python


def _populate_mod_list(reader: ModReader, mods: set[str]) -> tuple[list[str], dict[str, Any]]:
    mods.update({'base', 'core'})

    # Get all mods including dependencies
    mod_info: dict[str, Any] = {}
    load_order_constraints: dict[str, list[str]] = {}
    while True:
        new_mods = mods - mod_info.keys()
        if len(new_mods) == 0:
            break

        for mod in new_mods:
            reader.add_mod(mod)
            mod_info[mod] = json.loads(reader.get_text(f'__{mod}__/info.json'))

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


def _init_locale(reader: ModReader, mod_list: list[str]) -> dict[str, str]:
    locale: dict[str, str] = {}
    for mod in mod_list:
        prefix = ''
        for locale_file in reader.glob(f'__{mod}__/locale/en/*.cfg'):
            for line in reader.get_text(locale_file).splitlines():
                if not line or line[0] in ';#':
                    continue
                if line.startswith('['):
                    prefix = line[1:-1] + '.'
                    continue
                name, value = line.split('=', 1)
                locale[prefix + name] = value

    return locale


def _init_lua(reader: ModReader, base_dir: Path, quiet: bool) -> lupa.lua52.LuaRuntime:
    def lua_package_searcher(require_argument: str) -> Any:
        original_require_argument = require_argument

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
            if not lua.globals()['dir_stack']:
                return
            current_module = lua.globals()['dir_stack'][1]
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
                contents = reader.get_text(path)
            except FileNotFoundError:
                continue

            return lua.eval(
                '''
                (function(new_dir_stack_entry, contents, filename, original_require_argument)
                    return function ()
                        table.insert(dir_stack, 1, new_dir_stack_entry)
                        ret = load(contents, filename)(original_require_argument)
                        table.remove(dir_stack, 1)
                        return ret
                    end
                end)(...)''',
                new_dir_stack_entry,
                contents,
                path,
                original_require_argument)

    def lua_log(value: str) -> None:
        if not quiet:
            print(lua_table_to_python(value))

    lua = lupa.lua52.LuaRuntime(unpack_returned_tuples=True)
    serpent = (Path(__file__).parent / 'serpent.lua').read_text(encoding='utf-8')
    lua.execute('serpent = load(...)()', serpent, 'serpent')
    defines = (Path(__file__).parent / 'defines-1.1.110.lua').read_text(encoding='utf-8')
    lua.execute(defines)
    lua.globals()['package']['path'] = \
        f'{base_dir}/base/?.lua;{base_dir}/core/lualib/?.lua'
    lua.execute('table.insert(package.searchers, 1, ...)', lua_package_searcher)
    lua.globals()['log'] = lua_log
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


def _read_raw_data(lua: lupa.lua52.LuaRuntime, reader: ModReader, mod_list: list[str], mod_versions: dict[str, str]) -> Any:
    def maybe_execute(path: str) -> Any:
        try:
            text = reader.get_text(path)
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

    lua.globals()['mods'] = python_to_lua_table(lua, mod_versions)
    maybe_execute('__core__/lualib/dataloader.lua')
    for filename in ['settings', 'settings-updates', 'settings-final-fixes']:
        for mod in mod_list:
            maybe_execute(f'__{mod}__/{filename}.lua')
    raw_settings = lua_table_to_python(lua.globals()['data']['raw'])

    # Datatype: bool, int, etc.
    # Setting type: startup, runtime, etc.
    settings: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(lambda: None))
    for setting_datatype in ['bool', 'int', 'double', 'string']:
        if f'{setting_datatype}-setting' in raw_settings:
            for setting_name, data in raw_settings[f'{setting_datatype}-setting'].items():
                settings[data['setting_type']][setting_name] = {
                    'value': data['default_value']
                }

    # TODO incorporate settings from JSON or from live mod-settings:
    # read_tree_file('.../mod-settings.dat')
    lua.globals()['settings'] = settings

    for filename in ['data', 'data-updates', 'data-final-fixes']:
        for mod in mod_list:
            maybe_execute(f'__{mod}__/{filename}.lua')
    return lua_table_to_python(lua.globals()['data']['raw'])


def get_factorio_data(base_dir: Path, mod_cache_dir: Path, mods: list[str],
                      username: str, token: str, quiet: bool = False) -> Any:
    reader = ModReader(base_dir, mod_cache_dir, username, token)

    mod_list, mod_info = _populate_mod_list(reader, set(mods))
    mod_versions = {
            name: info.get('version', None)
            for name, info in mod_info.items()}
    locale = _init_locale(reader, mod_list)
    lua = _init_lua(reader, base_dir, quiet)
    raw = _read_raw_data(lua, reader, mod_list, mod_versions)

    return {
        'raw': raw,
        'locale': {
            'en': locale,
        },
        'mod_versions': mod_versions,
    }, reader
