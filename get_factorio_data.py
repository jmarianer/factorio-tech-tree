import io
import json
import lupa
import re

from icon import get_factorio_icon
from mod_reader import ModReader
from property_tree import read_tree_file
from utils import *

BASE='/Users/joeym/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/data'
MODS='/Users/joeym/Library/Application Support/Factorio/mods'
lua = lupa.LuaRuntime(unpack_returned_tuples=True)
reader = ModReader(BASE, MODS)


# TODO rename function and argument. Also go over and comment
def global_searcher(path):
    if not '/' in path:
        path = f'{path.replace(".", "/")}'
    if not path.endswith('.lua'):
        path += '.lua'

    if path.startswith('__'):
        paths = [path]
    else:
        if not lua.globals().dir_stack:
            return
        # TODO always trailing slash
        module = re.match('(__.*__/).*', lua.globals().dir_stack[1] + '/')[1]
        paths = [lua.globals().dir_stack[1] + '/' + path, module + path]

    for path in paths:
        path_elements = path.split('/')
        new_entry = '/'.join(path_elements[0:-1])

        try:
            contents = reader.get_text(path)
        except FileNotFoundError:
            continue

        return lua.eval('''
            (function(stack_entry, contents, filename)
                return function ()
                    table.insert(dir_stack, 1, stack_entry)
                    ret = load(contents, filename)()
                    table.remove(dir_stack, 1)
                    return ret
                end
            end)(...)''',
            new_entry,
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



lua.execute('table.insert(package.searchers, 4, ...)', global_searcher)
lua.execute('serpent = require("serpent")')
lua.globals().package.path = f'{BASE}/base/?.lua;{BASE}/core/lualib/?.lua'
lua.globals().settings = read_tree_file(f'{MODS}/mod-settings.dat')


# TODO make "defines" a Python dict instead
lua.execute('''
    require "util"

    function log(...)
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

    mods = {}
    function table_size(t)
        local count = 0
        for k,v in pairs(t) do
            count = count + 1
        end
        return count
    end
''')

lua.execute(reader.get_text('__core__/lualib/dataloader.lua'))
#mod_list = ['Krastorio2']
mod_list = ['Krastorio2', 'space-exploration', 'space-exploration-postprocess']

for m in mod_list:
    deps = [d.split(' ')[0]
            for d in json.loads(reader.get_text(f'__{m}__/info.json'))['dependencies']
            if d[0] not in "!(?)~"]
    for d in deps:
        if d not in mod_list:
            if d not in ['base', 'core']:
                mod_list.append(d)


mod_list.extend(['base', 'core'])
mod_list.reverse()
print(mod_list)

for m in mod_list:
    # TODO fix this
    lua.execute(f'mods["{m}"] = "1.2.3"')

lua.execute('print(mods.base)')
for f in ['data', 'data-updates', 'data-final-fixes']:
    for m in mod_list:
        try:
            text = reader.get_text(f'__{m}__/{f}.lua')
        except FileNotFoundError:
            continue

        lua.execute(f'''
            dir_stack = {{"__{m}__"}}
            for k, v in pairs(package.loaded) do
                package.loaded[k] = false
            end
        ''')
        lua.execute(text)

data = lua_table_to_python(lua.globals().data.raw)
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
