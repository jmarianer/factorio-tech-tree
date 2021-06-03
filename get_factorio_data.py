import re
import json
import lupa
from os import path

BASE='/Users/joeym/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/data'
lua = lupa.LuaRuntime(unpack_returned_tuples=True)


class LuaTableJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if lupa.lua_type(obj) == 'table':
            if all(isinstance(i, int) for i in obj.keys()):
                return list(obj.values())
            else:
                return {str(k): v for k, v in obj.items()}

        return json.JSONEncoder.default(self, obj)


def slurp(game_mod, filename):
    with open(f'{BASE}/{game_mod}/{filename}') as x:
        return x.read(), f'__{game_mod}__/{filename}'

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
lua.eval('require("__core__/data")')
lua.eval('require("__base__/data")')

data = lua.globals().data.raw

print(json.dumps(data, cls=LuaTableJsonEncoder, sort_keys=True, indent=4))
