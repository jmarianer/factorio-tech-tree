import click
import json
from pathlib import Path
from factorio_data import ModReader, get_factorio_data
from animation import get_animation, get_animation_specs
from utils import write_animation
from icon import get_factorio_icon, get_icon_specs
import concurrent.futures
import math


def sanitize_floats(obj):
    if isinstance(obj, dict):
        return {k: sanitize_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_floats(item) for item in obj]
    elif isinstance(obj, float):
        if math.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        elif math.isnan(obj):
            return "NaN"
    return obj


@click.group()
def cli() -> None:
    pass


def get_nested_value(obj, *keys):
    """Navigate through nested dict by checking each key in sequence."""
    for key in keys:
        if key in obj:
            obj = obj[key]
    return obj

def generate_icon(
    data_reader: ModReader,
    output_path: Path,
    type_name: str,
    name: str,
    object_data: dict
) -> None:
    if 'icon' in object_data or 'icons' in object_data:
        icon_spec = get_icon_specs(object_data)
        icon = get_factorio_icon(data_reader, icon_spec)
        icon.save(output_path / 'icons' / type_name / f'{name}.png')

def generate_assembling_machine_animation(
    data_reader: ModReader,
    output_path: Path,
    type_name: str,
    name: str,
    object_data: dict
) -> None:
    animation_data = (
        get_nested_value(object_data.get('animation', []), 'north', 'layers') +
        get_nested_value(object_data.get('idle_animation', []), 'north', 'layers')
    )
    
    if animation_data:
        write_animation(output_path / 'animations' / type_name / f'{name}.webp', animation_data, data_reader)

def generate_lab_animation(
    data_reader: ModReader,
    output_path: Path,
    type_name: str,
    name: str,
    object_data: dict
) -> None:
    animation_data = (
        get_nested_value(object_data.get('on_animation', []), 'north', 'layers')
    )
    
    if animation_data:
        write_animation(output_path / 'animations' / type_name / f'{name}.webp', animation_data, data_reader)

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
    data, reader = get_factorio_data(factorio_base, mod_cache_dir, mods, factorio_username, factorio_token, quiet)

    with open(output / 'data.json', 'w') as f:
        f.write(json.dumps(sanitize_floats(data), sort_keys=True, indent=4))

    # Create all icon and animation directories
    for type_name, objects in data['raw'].items():
        (output / 'icons' / type_name).mkdir(parents=True, exist_ok=True)
        (output / 'animations' / type_name).mkdir(parents=True, exist_ok=True)

    futures = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for type_name, objects in data['raw'].items():
            for name, object_data in objects.items():
                futures.append(executor.submit(generate_icon, reader, output, type_name, name, object_data))
                if type_name in ['assembling-machine', 'crafting-machine', 'rocket-silo', 'furnace']:
                    futures.append(executor.submit(generate_assembling_machine_animation, reader, output, type_name, name, object_data))
                if type_name == 'lab':
                    futures.append(executor.submit(generate_lab_animation, reader, output, type_name, name, object_data))

    for future in concurrent.futures.as_completed(futures):
        future.result()


if __name__ == '__main__':
    cli()