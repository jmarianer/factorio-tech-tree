import math
from typing import Any, Generator, Iterable, NamedTuple, Optional
from PIL import Image, ImageChops

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
    blend_mode: str

    def get_bounds(self) -> tuple[int, int, int, int]:
        x_start = self.shift[0] * 32 - self.width / 2 * self.scale
        y_start = self.shift[1] * 32 - self.height / 2 * self.scale
        x_end = x_start + self.width * self.scale
        y_end = y_start + self.height * self.scale
        return int(x_start), int(y_start), int(x_end), int(y_end)

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

        position = (
            self.x + col * self.width,
            self.y + row * self.height,
            self.x + (col+1) * self.width,
            self.y + (row+1) * self.height)
        size = (int(self.width * self.scale), int(self.height * self.scale))

        return raw.crop(position).resize(size)


def get_animation(reader: ModReader, spec: Iterable[Layer]) -> Generator[Image.Image, None, None]:
    layers = [l for l in spec if not l.draw_as_shadow]
    frame_count = math.lcm(*(l.frame_count for l in layers))
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
            layer_frame_no = frame_no % layer.frame_count

            image = layer.get_image(reader, layer_frame_no)
            shift_x, shift_y, _1, _2 = layer.get_bounds()
            offset = int(shift_x + x_origin), int(shift_y + y_origin)

            if layer.blend_mode == 'additive':
                # TODO
                # (1) There's got to be a better way to zero out all the alpha.
                # (2) Add the other blend modes. https://lua-api.factorio.com/1.1.110/types/BlendMode.html
                # (3) Consolidate this code with the icon.py code.
                offset_image = Image.new('RGBA', frame.size, (0, 0, 0, 0))
                offset_image.paste(image, offset)
                offset_image_data = list(offset_image.getdata())
                offset_image_data = list(map(lambda x: (x[0], x[1], x[2], 0), offset_image_data))
                offset_image.putdata(offset_image_data)  # type: ignore
                frame = ImageChops.add(frame, offset_image)
            else:  # normal
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
                stripes=s.get('stripes', None),
                blend_mode=s.get('blend_mode', 'normal'))