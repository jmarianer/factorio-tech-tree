import itertools

import click
import json
from jinja2 import Template
from shutil import copyfile
from typing import Any

from jinja_helpers import get_jinja_environment
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
def create_html(mod_cache_dir: str, factorio_base: str, factorio_username: str, factorio_token: str,
                mods: list[str], output: str, quiet: bool) -> None:
    data = FactorioData(factorio_base, mod_cache_dir, mods, factorio_username, factorio_token, quiet)

    all_techs = {
            name: data.technologies[name]
            for name, raw_tech in data.raw['technology'].items()
            if raw_tech.get('enabled', True)
            and 'count' in raw_tech['unit']}  # 'count' eliminates infinite research

    visible_recipes = [v for v in data.recipes.values() if not v.hidden]
    groups = sorted({recipe.subgroup.group for recipe in visible_recipes}, key=lambda g: g.order)
    grouped_recipes = itertools.groupby(
        itertools.groupby(
            sorted(visible_recipes, key=lambda r: (r.subgroup.group.order, r.subgroup.order, r.order)),
            key=lambda r: r.subgroup),
        key=lambda sg: sg[0].group)

    techs_in_order: list[str] = []
    while True:
        new_available = sorted(
                tech.name
                for tech in all_techs.values()
                if tech.prerequisite_names.issubset(techs_in_order)
                and tech.name not in techs_in_order)
        if len(new_available) == 0:
            break

        techs_in_order.extend(new_available)

    env = get_jinja_environment()

    def write_template(filename: str, template: Template, **kwargs: Any) -> None:
        with open(f'{output}/{filename}', 'w') as file:
            file.write(template.render(**kwargs))

    index_template = env.get_template('index.html')
    tech_template = env.get_template('tech.html')
    recipe_template = env.get_template('recipe.html')
    item_template = env.get_template('item.html')

    for tech in all_techs.values():
        tech.icon.save(f'{output}/tech_{tech.name}.png')
        write_template(
                f'tech_{tech.name}.html', tech_template,
                prerequisites=[all_techs[p] for p in tech.prerequisite_names if p in all_techs],
                tech=tech)

    for group in groups:
        group.icon.save(f'{output}/group_{group.name}.png')

    for recipe in data.recipes.values():
        recipe.icon.save(f'{output}/recipe_{recipe.name}.png')
        write_template(f'recipe_{recipe.name}.html', recipe_template, recipe=recipe)

    for item in data.items.values():
        item.icon.save(f'{output}/item_{item.name}.png')
        write_template(f'item_{item.name}.html', item_template, item=item)

    write_template(
            'index.html', index_template,
            # TODO make mod_info[m] a NamedTuple
            mod_list=sorted(data.mod_list, key=lambda m: str(data.mod_info[m]['title'])),
            mod_info=data.mod_info,
            techs=(all_techs[t] for t in techs_in_order),
            grouped_recipes=grouped_recipes,
    )

    copyfile('templates/factorio.css', f'{output}/factorio.css')
    copyfile('templates/clock-icon.png', f'{output}/clock-icon.png')


if __name__ == '__main__':
    cli()
