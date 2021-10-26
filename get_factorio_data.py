import itertools
import json
import math
from collections import namedtuple
from factorio_data import FactorioData


# CONFIG
SUPPORT='/Users/joeym/Library/Application Support'
BASE_DIR=f'{SUPPORT}/Steam/steamapps/common/Factorio/factorio.app/Contents/data'
MODS_DIR=f'{SUPPORT}/Factorio/mods'
MODS=['IndustrialRevolution']


# MAIN
print('Getting Factorio data...')
data = FactorioData(BASE_DIR, MODS_DIR, MODS)

print('Getting technology tree...')
Tech = namedtuple('Tuple', ['prerequisites', 'ingredients', 'recipes'])
all_techs = {
        k: Tech(
            prerequisites=set(v.get('prerequisites', [])),
            ingredients=v['unit']['ingredients'],
            recipes=[
                effect['recipe']
                for effect in v.get('effects', [])
                if 'recipe' in effect
            ])
        for k, v in data.raw['technology'].items() if v.get('enabled', True)}

prereqs_available = set()
positions = {}
for y in itertools.count(start=0):
    new_available = {
            k
            for k, v in all_techs.items()
            if v.prerequisites.issubset(prereqs_available)}
    if len(new_available - prereqs_available) == 0:
        break

    for x, tech_name in enumerate(new_available - prereqs_available):
        positions[tech_name] = (x, y)

    prereqs_available.update(new_available)

"""
print('Creating icons')
for tech_name, tech in all_techs.items():
    data.get_tech_icon(tech_name).save(f'output/tech_{tech_name}.png')
    for recipe_name in tech.recipes:
        data.get_recipe_icon(recipe_name).save(f'output/recipe_{recipe_name}.png')
    for ingredient in tech.ingredients:
        # TODO * on get_ingr!
        def get_ingr(i):
            if isinstance(i, list):
                return i[0]
            return i['name']
        ingredient_name = get_ingr(ingredient)
        data.get_item_icon(ingredient_name).save(f'output/item_{ingredient_name}.png')



        """

print('Outputing HTML')
with open('output/index.html', 'w') as index:
    index.write('''<html>
            <head>
                <title>Tech Tree</title>
                <link rel="stylesheet" href="../tech-tree.css" />
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js"></script>
                <script src="../tech-tree.js" charset="UTF-8"></script>
            </head>
            <body>
                <div id="tooltip">
                    <div id="tooltiptitle"></div>
                    <div id="tooltipproductsheading" class="tipheading">Products:</div>
                    <div id="tooltipproducts"></div>
                    <div id="tooltipingredientsheading" class="tipheading">Ingredients:</div>
                    <div id="tooltipingredients"></div>
                </div>
    ''')

    for tech_name, tech in all_techs.items():
        left, top = positions[tech_name]
        left = left * 101 + 20
        top = top * 168 + 34

        title = data.localize('technology-name', tech_name)
        prereqs = ','.join(tech.prerequisites)
        ingredients = ','.join(map(str, [a for b in tech.ingredients for a in b]))

        index.write(f'''<div
                style="left:{left}px;top:{top}px"
                id="{tech_name}"
                class="tech L1"
                data-prereqs="{prereqs}"
                data-title="{title}"
                data-ingredients="{ingredients}">
                    <img class="pic" src="tech_{tech_name}.png">
                <div class="items">''')

        for recipe_name in tech.recipes:
            name = data.localize('item-name', recipe_name)
            index.write(f'''<div
                    class="item"
                    id="item_{recipe_name}"
                    style="background-image:url(recipe_{recipe_name}.png)"
                    data-name="{name}">
                </div>''')

        index.write('''
                </div>
            </div>''')

    for t, tech in all_techs.items():
        for p in tech.prerequisites:
            # Draw a line from (x1, y1) to (x2, y2)
            x1, y1 = positions[t]
            x2, y2 = positions[p]

            x1 = x1 * 101 + 60
            x2 = x2 * 101 + 60
            y1 = y1 * 168 + 68
            y2 = y2 * 168 + 68

            xmid = (x1 + x2) / 2
            ymid = (y1 + y2) / 2
            angle = math.atan2((y2 - y1), (x2 - x1))
            length = math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)

            left = xmid - length / 2
            index.write(f'''
                <div
                    id="{t}_{p}"
                    class="path dark"
                    style="left:{left}px;top:{ymid}px;width:{length}px;transform:rotate({angle}rad)">
                </div>''')

    def get_ingr(i):
        if isinstance(i, list):
            return i[0]
        return i['name']
    all_ingredients = {get_ingr(a) for v in all_techs.values() for a in v.ingredients}
    for i in all_ingredients:
        data.get_item_icon(i).save(f'output/{i}.png')
        name = data.localize('item-name', i)
        index.write(f'''<div
            class="item"
            id="item_{i}"
            style="background-image:url(item_{i}.png)"
            data-name="{name}">
        </div>''')
