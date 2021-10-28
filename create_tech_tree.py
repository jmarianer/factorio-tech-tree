from collections import namedtuple
from jinja2 import Environment, FileSystemLoader

from factorio_data import FactorioData

# CONFIG
BASE_DIR='/Users/joeym/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/data'
MODS=['IndustrialRevolution']


# MAIN
print('Getting Factorio data...')
data = FactorioData(BASE_DIR, 'mod_cache', MODS)


print('Getting technology tree...')
# TODO Wonder what parts of this can go into factorio_data or some other helper module
Tech = namedtuple('Tech', ['name', 'time', 'localized_title', 'prerequisites', 'ingredients', 'recipes'])
Recipe = namedtuple('Recipe', ['name', 'localized_title', 'ingredients', 'products', 'time'])
Item = namedtuple('Item', ['name', 'amount', 'localized_title'])

def raw_to_item_list(raw_items):
    for raw_item in raw_items:
        if isinstance(raw_item, dict):
            name = raw_item['name']
            if 'amount' in raw_item:
                amount = raw_item['amount']
            else:
                amount = f'{raw_item["amount_min"]}–{raw_item["amount_max"]}'
        else:
            name, amount = raw_item
        yield Item(name, amount, data.localize_item(name))

def raw_to_recipe(raw_recipe):
    name = raw_recipe['name']

    if 'normal' in raw_recipe:
        raw_recipe = raw_recipe['normal']

    if 'results' in raw_recipe:
        results = raw_recipe['results']
    else:
        results = [[raw_recipe['result'], 1]]
    return Recipe(
            name=name,
            localized_title=data.localize_recipe(name),
            ingredients=list(raw_to_item_list(raw_recipe['ingredients'])),
            products=list(raw_to_item_list(results)),
            time=raw_recipe.get('energy_required', 0.5),
        )

all_recipes = {name: raw_to_recipe(raw_recipe)
               for name, raw_recipe in data.raw['recipe'].items()}

all_techs = {
        name: Tech(
            name=name,
            time=v['unit']['time'],
            localized_title=data.localize_tech(v),
            prerequisites=set(v.get('prerequisites', [])),
            ingredients=list(raw_to_item_list(v['unit']['ingredients'])),
            recipes=[all_recipes[effect['recipe']]
                     for effect in v.get('effects', [])
                     if 'recipe' in effect
            ])
        for name, v in data.raw['technology'].items()
        if v.get('enabled', True)}


prerequisites = set()
rows = []
while True:
    new_available = sorted(
            tech.name
            for tech in all_techs.values()
            if tech.prerequisites.issubset(prerequisites)
            and tech.name not in prerequisites)
    if len(new_available) == 0:
        break

    rows.append([all_techs[t] for t in new_available])

    prerequisites.update(new_available)


print('Creating icons')
for tech in all_techs.values():
    data.get_tech_icon(tech.name).save(f'output/tech_{tech.name}.png')

for recipe in all_recipes:
    data.get_recipe_icon(recipe).save(f'output/recipe_{recipe}.png')

all_items = {ingredient.name
             for tech in all_techs.values()
             for ingredient in tech.ingredients}
all_items.update({item.name
                  for recipe in all_recipes.values()
                  for item_list in [recipe.ingredients, recipe.products]
                  for item in item_list})
for item in all_items:
    data.get_item_icon(item).save(f'output/item_{item}.png')


env = Environment(loader=FileSystemLoader('.'), autoescape=True)
template = env.get_template('tech-tree.html')
with open('output/index.html', 'w') as index:
    index.write(template.render(tech_rows=rows))
