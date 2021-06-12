import configparser
import io
import json
import lupa
import math
import re

from defines import defines
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
locale = configparser.ConfigParser()


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
    

def localize(section, value):
    def get_localized_from_group(match):
        if match[1] == 'ENTITY':
            return localize('entity-name', match[2])
        elif match[1] == 'ITEM':
            return localize('item-name', match[2])
        else:
            return match[0]

    if value in locale[section]:
        localized = locale[section][value]
    else:
        match = re.match('(.*)-(\d+)$', value)
        if match:
            localized = locale[section].get(match[1], '???') + ' ' + match[2]
        else:
            localized = '???'
    return re.sub('__([^_]*)__([^_]*)__', get_localized_from_group, localized)


# MAIN
lua.execute('serpent = require("serpent")')
lua.globals().settings = read_tree_file(f'{MODS_DIR}/mod-settings.dat')
lua.globals().package.path = f'{BASE_DIR}/base/?.lua;{BASE_DIR}/core/lualib/?.lua'
lua.globals().defines = python_to_lua_table(lua, defines)
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
''')

populate_mod_list()
lua.globals().mods = lua.table(**mod_versions)


for mod in mod_list:
    for localefile in reader.glob(f'__{mod}__/locale/en/*.cfg'):
        locale.read_string('[EMPTYSECTION]\n' + reader.get_text(localefile))


lua.execute(reader.get_text('__core__/lualib/dataloader.lua'))
for lua_source_file in ['data', 'data-updates', 'data-final-fixes']:
    for mod in mod_list:
        try:
            text = reader.get_text(f'__{mod}__/{lua_source_file}.lua')
        except FileNotFoundError:
            continue

        # Reset package.loaded in between every module because some modules use
        # packages with identical names.
        lua.execute(f'''
            dir_stack = {{"__{mod}__/"}}
            for k, v in pairs(package.loaded) do
                package.loaded[k] = false
            end
        ''')
        lua.execute(text)

data = lua_table_to_python(lua.globals().data.raw)
# Dump All the Things if necessary
# print(json.dumps(data, sort_keys=True, indent=4))


# TODO: Here be dragons. This should really be a separate file (actually, everything preceding this should).
# HTML with embedded images for all techs in dependency order
print('''
<title>Tech Tree</title>
<link rel="stylesheet" href="https://davemcw.com/factorio/tech-tree/tech-tree.css" />
<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js"></script>
<script src="https://davemcw.com/factorio/tech-tree/tech-tree.js" charset="UTF-8"></script>
</head>
<body>
<div id="tooltip">
<div class="tiptitle"></div>
<div class="tip1 tipheading">Products:</div>
<div class="tip2"></div>
<div class="tip3 tipheading">Ingredients:</div>
<div class="tip4"></div>
</div>
''')
tech_and_prereqs = {
        k: set(v.get('prerequisites', []))
        for k, v in data['technology'].items()}
prereqs_available = set()
positions = {}
top = 34
while True:
    new_available = {
            k
            for k, v in tech_and_prereqs.items()
            if v.issubset(prereqs_available)}
    if len(new_available - prereqs_available) == 0:
        break

    left = 20
    for tech_name in new_available - prereqs_available:
        image = image_to_data_url(get_tech_icon(tech_name))
        title = localize('technology-name', tech_name)
        prereqs = ','.join(tech_and_prereqs[tech_name])
        positions[tech_name] = (left, top)
        print(f'<div style="left:{left}px;top:{top}px" id="{tech_name}" class="tech L1" data-prereqs="{prereqs}" data-title="{title}"><img class="pic" src="{image}"></div>')
        left += 101
    top += 168
    prereqs_available.update(new_available)

"""
wss: 727,34
mil: 828,202

midpoint: 818,153

767,68
40, 34
"""

for t in tech_and_prereqs:
    for p in tech_and_prereqs[t]:
        # Draw a line from (x1, y1) to (x2, y2)
        x1, y1 = positions[t]
        x2, y2 = positions[p]

        x1 += 40
        x2 += 40
        y1 += 34
        y2 += 34

        xmid = (x1 + x2) / 2
        ymid = (y1 + y2) / 2
        angle = math.atan2((y2 - y1), (x2 - x1))
        length = math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)

        left = xmid - length / 2
        print(f'<div id="{t}_{p}" class="path dark" style="left:{left}px;top:{ymid}px;width:{length}px;transform:rotate({angle}rad)"></div>')
