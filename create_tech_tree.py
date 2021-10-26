from collections import namedtuple
from jinja2 import Environment, FileSystemLoader

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
Tech = namedtuple('Tuple', ['name', 'prerequisites', 'ingredients', 'recipes'])
all_techs = {
        name: Tech(
            name=name,
            prerequisites=set(v.get('prerequisites', [])),
            ingredients=v['unit']['ingredients'],
            recipes=[
                effect['recipe']
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


env = Environment(loader=FileSystemLoader('.'), autoescape=True)
template = env.get_template("tech-tree.html")
with open('output/index.html', 'w') as index:
    index.write(template.render(tech_rows=rows))
