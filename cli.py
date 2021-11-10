import click
import json
from collections import namedtuple
from jinja2 import Environment, FileSystemLoader
from shutil import copyfile

from factorio_data import FactorioData


@click.group()
def cli():
    pass


@cli.command()
@click.option('--mod-cache-dir', default='mod_cache')
@click.option('--factorio-base', envvar='FACTORIO_BASE')
@click.option('--factorio-username', envvar='FACTORIO_USERNAME')
@click.option('--factorio-token', envvar='FACTORIO_TOKEN')
@click.option('--mods', multiple=True)
@click.option('--output', default='data.json')
@click.option('-q', '--quiet', is_flag=True)
def dump_data(mod_cache_dir, factorio_base, factorio_username, factorio_token, mods, output, quiet):
    data = FactorioData(factorio_base, mod_cache_dir, mods, factorio_username, factorio_token, quiet)
    with open(output, 'w') as f:
        f.write(json.dumps(data.raw, sort_keys=True, indent=4))


@cli.command()
@click.option('--mod-cache-dir', default='mod_cache')
@click.option('--factorio-base', envvar='FACTORIO_BASE')
@click.option('--factorio-username', envvar='FACTORIO_USERNAME')
@click.option('--factorio-token', envvar='FACTORIO_TOKEN')
@click.option('--mods', multiple=True)
@click.option('--output', default='output')
@click.option('-q', '--quiet', is_flag=True)
def create_tech_tree(mod_cache_dir, factorio_base, factorio_username, factorio_token, mods, output, quiet):
    data = FactorioData(factorio_base, mod_cache_dir, mods, factorio_username, factorio_token, quiet)

    # TODO None of this should be here...
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

    def raw_to_tech(raw_tech):
        count = raw_tech['unit']['count']
        ingredients = [
                Item(i.name, i.amount * count, i.localized_title)
                for i in raw_to_item_list(raw_tech['unit']['ingredients'])]
        return Tech(
                name=raw_tech['name'],
                time=raw_tech['unit']['time'] * count,
                localized_title=data.localize_tech(raw_tech),
                prerequisites=set(raw_tech.get('prerequisites', [])),
                ingredients=ingredients,
                recipes=[all_recipes[effect['recipe']]
                         for effect in raw_tech.get('effects', [])
                         if 'recipe' in effect])

    all_recipes = {name: raw_to_recipe(raw_recipe)
                   for name, raw_recipe in data.raw['recipe'].items()}

    all_techs = {
            name: raw_to_tech(raw_tech)
            for name, raw_tech in data.raw['technology'].items()
            if raw_tech.get('enabled', True)
            and 'count' in raw_tech['unit']}  # 'count' eliminates infinite research

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

    for tech in all_techs.values():
        data.get_tech_icon(tech.name).save(f'{output}/tech_{tech.name}.png')

    for recipe in all_recipes:
        data.get_recipe_icon(recipe).save(f'{output}/recipe_{recipe}.png')

    all_items = {ingredient.name
                 for tech in all_techs.values()
                 for ingredient in tech.ingredients}
    all_items.update({item.name
                      for recipe in all_recipes.values()
                      for item_list in [recipe.ingredients, recipe.products]
                      for item in item_list})
    for item in all_items:
        data.get_item_icon(item).save(f'{output}/item_{item}.png')

    env = Environment(loader=FileSystemLoader('.'), autoescape=True)
    template = env.get_template('tech-tree.html')
    with open(f'{output}/index.html', 'w') as index:
        index.write(template.render(tech_rows=rows))

    copyfile('tech-tree.css', f'{output}/tech-tree.css')
    copyfile('tech-tree.js', f'{output}/tech-tree.js')
    copyfile('clock-icon.png', f'{output}/clock-icon.png')


if __name__ == '__main__':
    cli()
