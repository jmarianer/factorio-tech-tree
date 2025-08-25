from dataclasses import dataclass
import itertools
import math
from typing import Any, Generator, Iterable, Optional
from PIL import Image, ImageChops

from mod_reader import ModReader


@dataclass
class Layer():
    height: int
    width: int
    x: int
    y: int
    frame_sequence: list[int]
    line_length: int
    scale: float
    shift: tuple[float, float]
    draw_as_glow: bool
    draw_as_light: bool
    draw_as_shadow: bool
    filename: Optional[str]
    stripes: Optional[list[dict[str, Any]]]
    blend_mode: str

    def get_bounds(self) -> tuple[int, int, int, int]:
        x_start = self.shift[0] * 32 - self.width / 2 * self.scale
        y_start = self.shift[1] * 32 - self.height / 2 * self.scale
        x_end = x_start + self.width * self.scale
        y_end = y_start + self.height * self.scale
        return int(x_start), int(y_start), int(x_end), int(y_end)

    def get_stripe(self, frame_no: int) -> dict[str, Any]:
        assert self.stripes is not None
        for stripe in self.stripes:
            stripe_frame_count = stripe['width_in_frames'] * stripe['height_in_frames']
            if frame_no >= stripe_frame_count:
                frame_no -= stripe_frame_count
            else:
                return stripe
        raise ValueError()

    def get_image(self, reader: ModReader, frame_no: int) -> Image.Image:
        frame_no = self.frame_sequence[frame_no] - 1
        if self.filename:
            raw = reader.get_image(self.filename, self.blend_mode != 'additive')
            row = frame_no // self.line_length
            col = frame_no % self.line_length
        else:
            stripe = self.get_stripe(frame_no)
            raw = reader.get_image(stripe['filename'], self.blend_mode != 'additive')
            row = frame_no // stripe['width_in_frames']
            col = frame_no % stripe['width_in_frames']

        position = (
            self.x + col * self.width,
            self.y + row * self.height,
            self.x + (col+1) * self.width,
            self.y + (row+1) * self.height)
        size = (int(self.width * self.scale), int(self.height * self.scale))

        return raw.crop(position).resize(size)


def get_animation(reader: ModReader, spec: Iterable[Layer]) -> Generator[Image.Image, None, None]:
    spec = list(spec)
    layers = [l for l in spec if l.draw_as_shadow] + [l for l in spec if not l.draw_as_shadow]
    frame_count = math.lcm(*(len(l.frame_sequence) for l in layers))
    bounding_boxes = [l.get_bounds() for l in layers]

    x_start = min(bb[0] for bb in bounding_boxes)
    y_start = min(bb[1] for bb in bounding_boxes)
    x_end = max(bb[2] for bb in bounding_boxes)
    y_end = max(bb[3] for bb in bounding_boxes)
    width = int(x_end - x_start)
    height = int(y_end - y_start)
    x_origin = width - x_end
    y_origin = height - y_end
    for frame_no in range(frame_count):
        frame = Image.new(mode='RGBA', size=(width, height))

        for layer in layers:
            layer_frame_no = frame_no % len(layer.frame_sequence)

            image = layer.get_image(reader, layer_frame_no)
            shift_x, shift_y, _1, _2 = layer.get_bounds()
            offset_x = int(shift_x + x_origin)
            offset_y = int(shift_y + y_origin)

            background = frame.crop((offset_x, offset_y, offset_x + image.width, offset_y + image.height))

            if layer.blend_mode == 'additive':
                # TODO
                # (1) Add the other blend modes. https://lua-api.factorio.com/1.1.110/types/BlendMode.html
                # (2) Consolidate this code with the icon.py code.
                result = ImageChops.add(background, image)
            else:  # normal
                result = Image.alpha_composite(background, image)

            frame.paste(result, (offset_x, offset_y))

        yield frame
    return


def get_layers(spec: Any) -> list[Layer]:
    if not spec:
        return []

    if 'layers' in spec:
        return list(itertools.chain.from_iterable(get_layers(s) for s in spec['layers']))

    spec.update(spec.get('hr_version', {}))
    run_mode = spec.get('run_mode', 'forward')
    frame_sequence = spec.get('frame_sequence', list(range(1, spec.get('frame_count', 1) + 1)))
    if run_mode == 'forward-then-backward':
        frame_sequence = frame_sequence + frame_sequence[-2:0:-1]
    elif run_mode == 'backward':
        frame_sequence = frame_sequence[::-1]

    return [Layer(
        height=spec['height'],
        width=spec['width'],
        x=spec.get('x', 0),
        y=spec.get('y', 0),
        line_length=spec.get('line_length', 1),
        scale=spec.get('scale', 1),
        shift=spec.get('shift', (0, 0)),
        draw_as_glow=spec.get('draw_as_glow', False),
        draw_as_light=spec.get('draw_as_light', False),
        draw_as_shadow=spec.get('draw_as_shadow', False),
        filename=spec.get('filename', None),
        stripes=spec.get('stripes', None),
        blend_mode=spec.get('blend_mode', 'normal'),
        frame_sequence=frame_sequence)]


def get_layers_2way(spec: Any) -> list[Layer]:
    layers = get_layers(spec)
    frame_count = math.lcm(*(len(l.frame_sequence) for l in layers))
    for l in layers:
        l.frame_sequence = l.frame_sequence * (frame_count // len(l.frame_sequence))
        l.frame_sequence = l.frame_sequence + list(reversed(l.frame_sequence))
    return layers


def get_layers_from_sprite4way(spec: Any, direction: str) -> list[Layer]:
    # TODO implement
    # See http://localhost:3000/angelbobs/entity/sea-pump-placeable
    # See http://localhost:3000/base/entity/pumpjack
    return []


def get_animation_specs(object: Any) -> dict[str, list[Layer]]:
    def fetch_from_4way(animation4way: Any, direction: str) -> list[Layer]:
        if 'north' not in animation4way:
            return get_layers(animation4way)
        if direction not in animation4way:
            return get_layers(animation4way['north'])
        return get_layers(animation4way[direction])

    def fetch_from_workingvis(workingvis: Any, direction: str) -> list[Layer]:
        if 'animation' in workingvis:
            return get_layers(workingvis['animation'])
        return get_layers(workingvis.get(f'{direction}_animation', {}))

    type = object['type']

    specs: dict[str, list[Layer]] = {}
    if type == 'lab':
        specs = {
            'on': get_layers(object['on_animation']),
            'off': get_layers(object['off_animation']),
        }

    if type in ['assembling-machine', 'crafting-machine', 'furnace']:
        for dir in ['north', 'south', 'east', 'west']:
            specs.update({
                # TODO always_draw_idle_animation
                dir: (
                    fetch_from_4way(object.get('animation', {}), dir) +
                    list(itertools.chain.from_iterable(
                        fetch_from_workingvis(workingvis, dir)
                        for workingvis in object.get('working_visualisations', [])
                    ))
                ),
            })

    if type == 'mining-drill':
        graphics_set = object.get('graphics_set', {})
        for dir in ['north', 'south', 'east', 'west']:
            specs.update({
                dir: (
                    get_layers_from_sprite4way(object.get('base_picture', {}), dir) +
                    fetch_from_4way(object.get('animations', {}), dir) +
                    fetch_from_4way(graphics_set.get('animation', {}), dir) +
                    fetch_from_4way(graphics_set.get('idle_animation', {}), dir) +
                    list(itertools.chain.from_iterable(
                        fetch_from_workingvis(workingvis, dir)
                        for workingvis in graphics_set.get('working_visualisations', [])
                    ))
                ),
            })

    if type == 'rocket-silo':
        specs = {
            'closed': (
                get_layers(object['shadow_sprite']) +
                get_layers(object['hole_sprite']) +
                get_layers(object['door_front_sprite']) +
                get_layers(object['door_back_sprite']) +
                get_layers(object['base_day_sprite']) +
                get_layers(object['base_front_sprite'])
            ),
            'open': (
                get_layers(object['shadow_sprite']) +
                get_layers(object['hole_sprite']) +
                get_layers(object['base_day_sprite']) +
                get_layers(object['base_front_sprite']) +
                get_layers_2way(object['arm_01_back_animation']) +
                get_layers_2way(object['arm_02_right_animation']) +
                get_layers_2way(object['arm_03_front_animation'])
            ),
        }

    return specs