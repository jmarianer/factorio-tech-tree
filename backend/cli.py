import click
import json
from pathlib import Path
from animation import get_animation_specs
from icon import get_icon_specs
from factorio_data import get_factorio_data
from utils import write_animation, write_icon, sanitize_floats
import concurrent.futures

@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--mod-cache-dir', default='mod_cache', type=click.Path(file_okay=False, dir_okay=True, path_type=Path))
@click.option('--factorio-base', envvar='FACTORIO_BASE', type=click.Path(file_okay=False, dir_okay=True, path_type=Path))
@click.option('--factorio-username', envvar='FACTORIO_USERNAME')
@click.option('--factorio-token', envvar='FACTORIO_TOKEN')
@click.option('--output', type=click.Path(file_okay=False, dir_okay=True, path_type=Path))
@click.option('-q', '--quiet', is_flag=True)
@click.argument('config_file', type=click.Path(file_okay=True, dir_okay=False, path_type=Path))
def dump_data(mod_cache_dir: Path, factorio_base: Path, factorio_username: str, factorio_token: str,
              output: Path, quiet: bool, config_file: Path) -> None:
    with open(config_file) as f:
        config = json.load(f)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures: list[concurrent.futures.Future[None]] = []
        for regime, c in config.items():
            (output / regime).mkdir(parents=True, exist_ok=True)
            data, reader = get_factorio_data(factorio_base, mod_cache_dir, c["mods"], factorio_username, factorio_token, quiet)

            with open(output / regime / 'data.json', 'w') as f:
                f.write(json.dumps(sanitize_floats(data), sort_keys=True, indent=4))

            for type_name, objects in data['raw'].items():
                (output / regime / 'icons' / type_name).mkdir(parents=True, exist_ok=True)

            for type_name, objects in data['raw'].items():
                for name, object_data in objects.items():
                    if 'icon' in object_data or 'icons' in object_data:
                        futures.append(executor.submit(write_icon, output / regime / 'icons' / type_name / f'{name}.png', get_icon_specs(object_data), reader))

                    animations = get_animation_specs(object_data)
                    if animations:
                        base_path = (output / regime / 'animations' / type_name / name)
                        base_path.mkdir(parents=True, exist_ok=True)
                        for k, v in animations.items():
                            futures.append(executor.submit(write_animation, base_path / f'{k}.webp', v, reader))

        concurrent.futures.wait(futures)

    with open(output / 'config.json', 'w') as f:
        f.write(json.dumps(config, sort_keys=True, indent=4))


@cli.command()
@click.option('--mod-cache-dir', default='mod_cache', type=click.Path(file_okay=False, dir_okay=True, path_type=Path))
@click.option('--factorio-base', envvar='FACTORIO_BASE', type=click.Path(file_okay=False, dir_okay=True, path_type=Path))
@click.option('--factorio-username', envvar='FACTORIO_USERNAME')
@click.option('--factorio-token', envvar='FACTORIO_TOKEN')
@click.option('--output', type=click.Path(file_okay=False, dir_okay=True, path_type=Path))
@click.option('-q', '--quiet', is_flag=True)
@click.argument('config_file', type=click.Path(file_okay=True, dir_okay=False, path_type=Path))
@click.argument('regime')
@click.argument('type')
@click.argument('name')
def generate_animation(
        mod_cache_dir: Path, factorio_base: Path, factorio_username: str, factorio_token: str,
        output: Path, quiet: bool, config_file: Path, regime: str, type: str, name: str) -> None:
    with open(config_file) as f:
        config = json.load(f)
    data, reader = get_factorio_data(factorio_base, mod_cache_dir, config[regime]["mods"], factorio_username, factorio_token, quiet)
    object = data['raw'][type][name]
    print(json.dumps(object, sort_keys=True, indent=4))
    for name, value in get_animation_specs(object).items():
        write_animation(output / f'{name}.webp', value, reader)

if __name__ == '__main__':
    cli()