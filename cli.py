import click
import json
from jinja2 import Environment, FileSystemLoader
from shutil import copyfile

from factorio_data import FactorioData


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--mod-cache-dir', default='mod_cache')
@click.option('--factorio-base', envvar='FACTORIO_BASE')
@click.option('--factorio-username', envvar='FACTORIO_USERNAME')
@click.option('--factorio-token', envvar='FACTORIO_TOKEN')
@click.option('--mods', multiple=True)
@click.option('--output', default='data.json')
@click.option('-q', '--quiet', is_flag=True)
def dump_data(mod_cache_dir: str, factorio_base: str, factorio_username: str, factorio_token: str,
              mods: list[str], output: str, quiet: bool) -> None:
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
def create_tech_tree(mod_cache_dir: str, factorio_base: str, factorio_username: str, factorio_token: str,
                     mods: list[str], output: str, quiet: bool) -> None:
    data = FactorioData(factorio_base, mod_cache_dir, mods, factorio_username, factorio_token, quiet)

    all_recipes = {name: data.get_recipe(name)
                   for name in data.raw['recipe']}

    all_techs = {
            name: data.get_tech(name)
            for name, raw_tech in data.raw['technology'].items()
            if raw_tech.get('enabled', True)
            and 'count' in raw_tech['unit']}  # 'count' eliminates infinite research

    prerequisites: set[str] = set()
    rows = []
    while True:
        new_available = sorted(
                tech.name
                for tech in all_techs.values()
                if tech.prerequisite_names.issubset(prerequisites)
                and tech.name not in prerequisites)
        if len(new_available) == 0:
            break

        rows.append([all_techs[t] for t in new_available])

        prerequisites.update(new_available)

    for tech in all_techs.values():
        tech.icon.save(f'{output}/tech_{tech.name}.png')

    for recipe in all_recipes.values():
        recipe.icon.save(f'{output}/recipe_{recipe.name}.png')

    all_items = {ingredient.name
                 for tech in all_techs.values()
                 for ingredient in tech.ingredients}
    all_items.update({item.name
                      for recipe in all_recipes.values()
                      for item_list in [recipe.ingredients, recipe.products]
                      for item in item_list})
    for item in all_items:
        data.get_item(item).icon.save(f'{output}/item_{item}.png')

    env = Environment(loader=FileSystemLoader('.'), autoescape=True)
    template = env.get_template('tech-tree.html')
    with open(f'{output}/index.html', 'w') as index:
        index.write(template.render(tech_rows=rows))

    copyfile('tech-tree.css', f'{output}/tech-tree.css')
    copyfile('tech-tree.js', f'{output}/tech-tree.js')
    copyfile('clock-icon.png', f'{output}/clock-icon.png')


if __name__ == '__main__':
    cli()
