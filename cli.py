import click
import json

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
def dump_data(mod_cache_dir, factorio_base, factorio_username, factorio_token, mods, output):
    data = FactorioData(factorio_base, mod_cache_dir, mods, factorio_username, factorio_token)
    click.echo(data.mod_versions)
    with open(output, 'w') as f:
        f.write(json.dumps(data.raw, sort_keys=True, indent=4))


if __name__ == '__main__':
    cli()
