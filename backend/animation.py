import math
from typing import Any, Generator, Iterable, NamedTuple, Optional
from PIL import Image

from mod_reader import ModReader


class Layer(NamedTuple):
    height: int
    width: int
    x: int
    y: int
    frame_count: int
    line_length: int
    scale: float
    shift: tuple[float, float]
    draw_as_glow: bool
    draw_as_light: bool
    draw_as_shadow: bool
    filename: Optional[str]
    stripes: Optional[list[dict[str, Any]]]

    def get_image(self, reader: ModReader, frame_no: int) -> Image.Image:
        if self.filename:
            raw = reader.get_image(self.filename)
            row = frame_no // self.line_length
            col = frame_no % self.line_length
        else:
            assert self.stripes is not None
            for stripe in self.stripes:
                stripe_frame_count = stripe['width_in_frames'] * stripe['height_in_frames']
                if frame_no >= stripe_frame_count:
                    frame_no -= stripe_frame_count
                else:
                    break

            raw = reader.get_image(stripe['filename'])
            row = frame_no // stripe['width_in_frames']
            col = frame_no % stripe['width_in_frames']

        return raw.crop((
            self.x + col * self.width,
            self.y + row * self.height,
            self.x + (col+1) * self.width,
            self.y + (row+1) * self.height))


def get_animation(reader: ModReader, spec: Iterable[Layer]) -> Generator[Image.Image, None, None]:
    layers = [l for l in spec if not l.draw_as_shadow and not l.draw_as_light]
    frame_count = math.lcm(*(l.frame_count for l in layers))

    x_start = min(layer.shift[0] * 64 for layer in layers)
    y_start = min(layer.shift[1] * 64 for layer in layers)
    x_end = max(layer.shift[0] * 64 + layer.width for layer in layers)
    y_end = max(layer.shift[1] * 64 + layer.height for layer in layers)
    width = int(x_end - x_start)
    height = int(y_end - y_start)
    x_origin = width / 2 - x_start
    y_origin = height / 2 - y_start
    for frame_no in range(frame_count):
        frame = Image.new(mode='RGBA', size=(width, height))

        for layer in layers:
            layer_frame_no = frame_no % layer.frame_count

            image = layer.get_image(reader, layer_frame_no)
            shift_x, shift_y = layer.shift
            shift_x *= 64
            shift_y *= 64
            shift_x += x_origin - layer.width / 2
            shift_y += y_origin - layer.height / 2
            offset = int(shift_x), int(shift_y)

            frame.alpha_composite(image, offset)

        yield frame
    return


def get_animation_specs(spec: Any) -> Generator[Layer, None, None]:
    for s in spec:
        if 'layers' in s:
            yield from get_animation_specs(s)
        else:
            s.update(s.get('hr_version', {}))
            yield Layer(
                height=s['height'],
                width=s['width'],
                x=s.get('x', 0),
                y=s.get('y', 0),
                frame_count=s.get('frame_count', 1),
                line_length=s.get('line_length', 1),
                scale=s.get('scale', 1),
                shift=s.get('shift', (0, 0)),
                draw_as_glow=s.get('draw_as_glow', False),
                draw_as_light=s.get('draw_as_light', False),
                draw_as_shadow=s.get('draw_as_shadow', False),
                filename=s.get('filename', None),
                stripes=s.get('stripes', None))