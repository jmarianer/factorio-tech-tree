from typing import Any
import click
import json
from pathlib import Path
from factorio_data import ModReader, get_factorio_data
from utils import write_animation, write_icon, sanitize_floats
import concurrent.futures

@click.group()
def cli() -> None:
    pass


def get_nested_value(obj: Any, *keys: str):
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
    object_data: dict[Any, Any]
) -> None:
    if 'icon' in object_data or 'icons' in object_data:
        write_icon(output_path / 'icons' / type_name / f'{name}.png', object_data, data_reader)

def generate_assembling_machine_animation(
    data_reader: ModReader,
    output_path: Path,
    type_name: str,
    name: str,
    object_data: dict[Any, Any]
) -> None:
    animation_data: list[Any] = []
    def add_animation_data(animation: Any):
        if 'layers' in animation:
            animation_data.extend(animation['layers'])
        else:
            animation_data.append(animation)

    if 'animation' in object_data:
        add_animation_data(get_nested_value(object_data['animation'], 'north'))
    if 'idle_animation' in object_data:
        add_animation_data(get_nested_value(object_data['idle_animation'], 'north'))
    if 'working_visualisations' in object_data:
        for s in object_data['working_visualisations']:
            if 'animation' in s:
                add_animation_data(s['animation'])

    if animation_data:
        write_animation(output_path / 'animations' / type_name / f'{name}.webp', animation_data, data_reader)

def generate_mining_drill_animation(
    data_reader: ModReader,
    output_path: Path,
    type_name: str,
    name: str,
    object_data: dict[Any, Any]
) -> None:
    animation_data: list[Any] = []
    if 'animation' in object_data:
        animation_data.extend(get_nested_value(object_data['animation'], 'north', 'layers'))
    graphics_set = object_data.get('graphics_set', {})
    if 'animation' in graphics_set:
        animation_data.extend(get_nested_value(graphics_set['animation'], 'north', 'layers'))
    if 'idle_animation' in graphics_set:
        animation_data.extend(get_nested_value(graphics_set['idle_animation'], 'north', 'layers'))
    if 'working_visualisations' in graphics_set:
        for s in graphics_set['working_visualisations']:
            animation = s.get('animation', s.get('north_animation', {}))
            if animation:
                if 'layers' in animation:
                    animation_data.extend(animation['layers'])
                else:
                    animation_data.append(animation)
    if animation_data:
        write_animation(output_path / 'animations' / type_name / f'{name}.webp', animation_data, data_reader)

def generate_lab_animation(
    data_reader: ModReader,
    output_path: Path,
    type_name: str,
    name: str,
    object_data: dict[Any, Any]
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

            # Create all icon and animation directories
            for type_name, objects in data['raw'].items():
                (output / regime / 'icons' / type_name).mkdir(parents=True, exist_ok=True)
                (output / regime / 'animations' / type_name).mkdir(parents=True, exist_ok=True)

            for type_name, objects in data['raw'].items():
                for name, object_data in objects.items():
                    futures.append(executor.submit(generate_icon, reader, output / regime, type_name, name, object_data))
                    if type_name in ['assembling-machine', 'crafting-machine', 'rocket-silo', 'furnace']:
                        futures.append(executor.submit(generate_assembling_machine_animation, reader, output / regime, type_name, name, object_data))
                    if type_name == 'lab':
                        futures.append(executor.submit(generate_lab_animation, reader, output / regime, type_name, name, object_data))
                    if type_name == 'mining-drill':
                        futures.append(executor.submit(generate_mining_drill_animation, reader, output / regime, type_name, name, object_data))

        concurrent.futures.wait(futures)

    with open(output / 'config.json', 'w') as f:
        f.write(json.dumps(config, sort_keys=True, indent=4))


if __name__ == '__main__':
    cli()