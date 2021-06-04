import base64
import io
import json
import lupa
import re
from PIL import Image, ImageOps, ImageColor
from os import path

BASE='/Users/joeym/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/data'
lua = lupa.LuaRuntime(unpack_returned_tuples=True)


def lua_table_to_python(obj):
    if lupa.lua_type(obj) == 'table':
        if all(isinstance(i, int) for i in obj.keys()):
            return [lua_table_to_python(v) for v in obj.values()]
        else:
            return {str(k): lua_table_to_python(v) for k, v in obj.items()}
    elif lupa.lua_type(obj) is not None:
        return lupa.lua_type(obj)
    else:
        return obj


def slurp(game_mod, filename):
    with open(f'{BASE}/{game_mod}/{filename}') as x:
        return x.read(), f'__{game_mod}__/{filename}'


def get_binary(path):
    match = re.match('__(.*)__/(.*)', path)
    if not match:
        return None

    game_mod = match[1]
    filename = match[2]

    with open(f'{BASE}/{game_mod}/{filename}', 'rb') as x:
        return x.read()


def load(game_mod, module):
    return slurp(game_mod, f'{module.replace(".", "/")}.lua')
        

def create_local_searcher(game_mod):
    def local_searcher(module):
        try:
            return lua.eval('load(...)', *load(game_mod, module))
        except FileNotFoundError:
            pass
    return local_searcher


def global_searcher(path):
    match = re.match('__(.*)__/(.*)', path)
    if not match:
        return None

    game_mod = match[1]
    module = match[2]

    ret = lua.eval('''
        (function(searcher, contents, filename)
            return function ()
                table.insert(package.searchers, 1, searcher)
                ret = load(contents, filename)()
                table.remove(package.searchers, 1)
                return ret
            end
        end)(...)''',
        create_local_searcher(game_mod), *load(game_mod, module))

    return ret


def get_icon(icon_specs):
    icon_size = icon_specs[0]['icon_size']
    icon = Image.new(mode='RGBA', size=(icon_size, icon_size))
    for icon_spec in icon_specs:
        layer_original_size = icon_spec.get('icon_size', icon_size)
        layer_scaled_size = int(layer_original_size * icon_spec.get('scale', 1))

        layer = Image \
                .open(io.BytesIO(get_binary(icon_spec['icon']))) \
                .crop([0, 0, layer_original_size, layer_original_size]) \
                .convert('RGBA') \
                .resize((layer_scaled_size, layer_scaled_size))

        if 'tint' in icon_spec:
            tint = icon_spec['tint']
            layer_grayscale = ImageOps.grayscale(layer).getdata()
            layer_alpha = layer.getdata(3)

            layer_new_data = map(
                    lambda grayscale, alpha: (
                        int(grayscale * tint['r']),
                        int(grayscale * tint['g']),
                        int(grayscale * tint['b']),
                        int(alpha * tint['a'])),
                    layer_grayscale, layer_alpha)
            layer.putdata(list(layer_new_data))



        shift_x, shift_y = icon_spec.get('shift', (0, 0))
        default_offset = (icon_size - layer_scaled_size) / 2
        offset = tuple(map(int, (default_offset + shift_x, default_offset + shift_y)))

        icon.alpha_composite(layer, offset)

    return icon


def get_icon_specs(a_dict):
    return a_dict['icons'] if 'icons' in a_dict else [{
        'icon': a_dict['icon'],
        'icon_size': a_dict['icon_size'],
        }]


def get_item_icon(item_name):
    return get_icon(get_icon_specs(data['item'][item_name]))


def get_tech_icon(tech_name):
    return get_icon(get_icon_specs(data['technology'][tech_name]))


def get_recipe_icon(recipe_name):
    recipe = data['recipe'][recipe_name]
    try:
        spec = get_icon_specs(recipe)
    except KeyError:
        main_item_name = recipe.get('main_product', recipe['results'][0]['name'])
        item = data['item'][main_item_name]
        spec = get_icon_specs(item)

    return get_icon(spec)


def image_to_data_url(image):
    stream = io.BytesIO()
    image.save(stream, 'png')
    encoded = base64.b64encode(stream.getvalue()).decode('ascii')
    return 'data:image/jpeg;base64,' + encoded

lua.eval('table.insert(package.searchers, 1, ...)', global_searcher)
lua.globals().package.path = f'{BASE}/core/lualib/?.lua;{BASE}/base/?.lua'

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
''')

lua.execute(slurp('core', 'lualib/dataloader.lua')[0])
# TODO automate this. Need an "if exists" thing.
# for f in ['data', 'data-updates', 'data-final-fixes']:
#     lua.eval(f'require("__core__/{f}")')
#     lua.eval(f'require("__base__/{f}")')

# The stupid way:
lua.eval('require("__core__/data")')
lua.eval('require("__base__/data")')
lua.eval('require("__base__/data-updates")')

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
        print(f'<img src="{image_to_data_url(get_tech_icon(tech_name))}">')
    prereqs_available.update(new_available)
