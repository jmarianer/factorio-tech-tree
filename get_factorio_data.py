import io
import json
import lupa
import re

from icon import get_factorio_icon
from mod_reader import ModReader
from property_tree import read_tree_file
from utils import *


# CONFIG
SUPPORT='/Users/joeym/Library/Application Support'
BASE_DIR=f'{SUPPORT}/Steam/steamapps/common/Factorio/factorio.app/Contents/data'
MODS_DIR=f'{SUPPORT}/Factorio/mods'
MODS=['Krastorio2', 'space-exploration', 'space-exploration-postprocess']


# GLOBALS
lua = lupa.LuaRuntime(unpack_returned_tuples=True)
reader = ModReader(BASE_DIR, MODS_DIR)
mod_list = []
mod_versions = {}


# FUNCTIONS
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
        if not lua.globals().dir_stack:
            return
        current_module = lua.globals().dir_stack[1]
        game_mod_root = re.match('(__.*__/).*', current_module)[1]
        paths = [current_module + require_argument, game_mod_root + require_argument]

    for path in paths:
        path_elements = path.split('/')
        new_dir_stack_entry = '/'.join(path_elements[0:-1]) + '/'

        try:
            contents = reader.get_text(path)
        except FileNotFoundError:
            continue

        return lua.eval('''
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


def get_icon_specs(a_dict):
    return a_dict['icons'] if 'icons' in a_dict else [{
        'icon': a_dict['icon'],
        'icon_size': a_dict['icon_size'],
        }]


def get_item_icon(item_name):
    return get_factorio_icon(reader, get_icon_specs(data['item'][item_name]))


def get_tech_icon(tech_name):
    return get_factorio_icon(reader, get_icon_specs(data['technology'][tech_name]))


def get_recipe_icon(recipe_name):
    recipe = data['recipe'][recipe_name]
    try:
        spec = get_icon_specs(recipe)
    except KeyError:
        main_item_name = recipe.get('main_product', recipe['results'][0]['name'])
        item = data['item'][main_item_name]
        spec = get_icon_specs(item)

    return get_factorio_icon(reader, spec)


def populate_mod_list():
    global mod_list, mod_versions
    mod_list = []

    mods = set(MODS)
    mods.update({'base', 'core'})

    # Get all mods including dependencies
    load_order_constraints = {}
    while True:
        new_mods = mods - mod_versions.keys()
        if len(new_mods) == 0:
            break

        for mod in new_mods:
            info_json = json.loads(reader.get_text(f'__{mod}__/info.json'))
            mod_versions[mod] = info_json.get('version', None)
            # ! for incompatibility
            # ? for an optional dependency
            # (?) for a hidden optional dependency
            # ~ for a dependency that does not affect load order
            # or no prefix for a hard requirement for the other mod.

            # Get all required dependencies, and also all optional dependencies that affect load order
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
    

# MAIN
lua.execute('serpent = require("serpent")')
lua.globals().settings = read_tree_file(f'{MODS_DIR}/mod-settings.dat')
lua.globals().package.path = f'{BASE_DIR}/base/?.lua;{BASE_DIR}/core/lualib/?.lua'
lua.execute('table.insert(package.searchers, 4, ...)', lua_package_searcher)
lua.execute('''
    require "util"

    function log(...)
    end

    function table_size(t)
        local count = 0
        for k,v in pairs(t) do
            count = count + 1
        end
        return count
    end

    defines = {}
    defines.alert_type = {}
    defines.behavior_result = {}
    defines.build_check_type = {}
    defines.chain_signal_state = {}
    defines.chunk_generated_status = {}
    defines.circuit_condition_index = {}
    defines.circuit_connector_id = {}
    defines.command = {}
    defines.compound_command = {}
    defines.control_behavior = {}
    defines.control_behavior.inserter = {}
    defines.control_behavior.inserter.circuit_mode_of_operation = {}
    defines.control_behavior.inserter.hand_read_mode = {}
    defines.control_behavior.logistics_container = {}
    defines.control_behavior.logistics_container.circuit_mode_of_operation = {}
    defines.control_behavior.lamp = {}
    defines.control_behavior.lamp.circuit_mode_of_operation = {}
    defines.control_behavior.mining_drill = {}
    defines.control_behavior.mining_drill.resource_read_mode = {}
    defines.control_behavior.transport_belt = {}
    defines.control_behavior.transport_belt.content_read_mode = {}
    defines.control_behavior.type = {}
    defines.controllers = {}
    defines.deconstruction_item = {}
    defines.deconstruction_item.entity_filter_mode = {}
    defines.deconstruction_item.tile_filter_mode = {}
    defines.deconstruction_item.tile_selection_mode = {}
    defines.difficulty = {}
    defines.difficulty_settings = {}
    defines.difficulty_settings.recipe_difficulty = {}
    defines.difficulty_settings.technology_difficulty = {}
    defines.difficulty_settings.recipe_difficulty.normal = 1
    defines.difficulty_settings.technology_difficulty.normal = 1
    defines.distraction = {}
    defines.direction = {}
    defines.direction.north = 1
    defines.direction.east = 2
    defines.direction.south = 3
    defines.direction.west = 4
    defines.direction.northeast = 5
    defines.direction.southeast = 6
    defines.direction.southwest = 7
    defines.direction.northwest = 8
    defines.entity_status = {}
    defines.events = {}
    defines.flow_precision_index = {}
    defines.group_state = {}
    defines.gui_type = {}
    defines.input_action = {}
    defines.inventory = {}
    defines.logistic_member_index = {}
    defines.logistic_mode = {}
    defines.mouse_button_type = {}
    defines.rail_connection_direction = {}
    defines.rail_direction = {}
    defines.render_mode	= {}
    defines.rich_text_setting = {}
    defines.riding = {}
    defines.riding.acceleration = {}
    defines.riding.direction = {}
    defines.shooting = {}
    defines.signal_state = {}
    defines.train_state	 = {}
    defines.transport_line = {}
    defines.wire_connection_id = {}
    defines.wire_type = {}
''')

populate_mod_list()
lua.globals().mods = lua.table(**mod_versions)

lua.execute(reader.get_text('__core__/lualib/dataloader.lua'))

for f in ['data', 'data-updates', 'data-final-fixes']:
    for m in mod_list:
        print(m, f)
        try:
            text = reader.get_text(f'__{m}__/{f}.lua')
        except FileNotFoundError:
            continue

        lua.execute(f'''
            dir_stack = {{"__{m}__/"}}
            for k, v in pairs(package.loaded) do
                package.loaded[k] = false
            end
        ''')
        lua.execute(text)

data = lua_table_to_python(lua.globals().data.raw)
exit()
# Dump All the Things if necessary
# print(json.dumps(data, sort_keys=True, indent=4))

# Test 1: Something to do with prerequisites
tech = data['technology']
prereqs_available = set()
while True:
    new_available = {
            k
            for k, v in tech.items()
            if set(v.get('prerequisites', [])).issubset(prereqs_available)}
    if len(new_available - prereqs_available) == 0:
        break
    for tech_name in new_available - prereqs_available:
        print(f'<img style="width:32; height:32" src="{image_to_data_url(get_tech_icon(tech_name))}" title="{tech_name}">')
    prereqs_available.update(new_available)
