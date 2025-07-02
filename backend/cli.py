import click
import json
from pathlib import Path
from factorio_data import FactorioData
from icon import get_factorio_icon, get_icon_specs


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--mod-cache-dir', default='mod_cache', type=click.Path(file_okay=False, dir_okay=True, path_type=Path))
@click.option('--factorio-base', envvar='FACTORIO_BASE', type=click.Path(file_okay=False, dir_okay=True, path_type=Path))
@click.option('--factorio-username', envvar='FACTORIO_USERNAME')
@click.option('--factorio-token', envvar='FACTORIO_TOKEN')
@click.option('--mods', multiple=True)
@click.option('--output', type=click.Path(file_okay=False, dir_okay=True, path_type=Path))
@click.option('-q', '--quiet', is_flag=True)
def dump_data(mod_cache_dir: Path, factorio_base: Path, factorio_username: str, factorio_token: str,
              mods: list[str], output: Path, quiet: bool) -> None:
    data = FactorioData(factorio_base, mod_cache_dir, mods, factorio_username, factorio_token, quiet)
    with open(output / 'data.json', 'w') as f:
        f.write(json.dumps(data.raw, sort_keys=True, indent=4))

    object = data.raw['airborne-pollutant']['pollution']
    icon_spec = get_icon_specs(object)
    icon = get_factorio_icon(data.reader, icon_spec)

    for type, objects in data.raw.items():
        (output / 'icons' / type).mkdir(parents=True, exist_ok=True)
        for name, object in objects.items():
            if 'icon' in object or 'icons' in object:
                print(f'Generating icon for {type} {name}')
                icon_spec = get_icon_specs(object)
                icon = get_factorio_icon(data.reader, icon_spec)
                icon.save(output / 'icons' / type / f'{name}.png')


if __name__ == '__main__':
    cli()