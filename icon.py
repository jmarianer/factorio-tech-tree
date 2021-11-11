import io
from typing import Any, Optional, NamedTuple
from PIL import Image, ImageOps

from mod_reader import ModReader


# TODO Get layers to not be an Any
class IconSpec(NamedTuple):
    size: int
    layers: list[Any]


def get_factorio_icon(reader: ModReader, icon_spec: IconSpec) -> Image.Image:
    icon_size = icon_spec.size
    icon = Image.new(mode='RGBA', size=(icon_size, icon_size))
    x1: Optional[int] = None
    x2: Optional[int] = None
    y1: Optional[int] = None
    y2: Optional[int] = None
    for icon_layer in icon_spec.layers:
        layer_original_size = icon_layer.get('icon_size', icon_size)
        layer_scaled_size = int(layer_original_size * icon_layer.get('scale', 1))

        layer = Image \
            .open(io.BytesIO(reader.get_binary(icon_layer['icon']))) \
            .crop((0, 0, layer_original_size, layer_original_size)) \
            .convert('RGBA') \
            .resize((layer_scaled_size, layer_scaled_size))

        if 'tint' in icon_layer:
            tint = icon_layer['tint']
            if isinstance(tint, list):
                tint = {
                    'r': tint[0],
                    'g': tint[1],
                    'b': tint[2],
                    'a': tint[3],
                }
            layer_grayscale = ImageOps.grayscale(layer).getdata()
            layer_alpha = layer.getdata(3)

            layer_new_data = map(
                    lambda grayscale, alpha: (
                        int(grayscale * tint['r']),
                        int(grayscale * tint['g']),
                        int(grayscale * tint['b']),
                        int(alpha * tint.get('a', 1))),
                    layer_grayscale, layer_alpha)
            # TODO Not sure but I think the type of layer.putdata is just wrong in the stub.
            layer.putdata(list(layer_new_data))  # type: ignore

        shift_x, shift_y = icon_layer.get('shift', (0, 0))
        default_offset = (icon_size - layer_scaled_size) / 2
        shift_x += default_offset
        shift_y += default_offset
        offset = int(shift_x), int(shift_y)

        icon.alpha_composite(layer, offset)

        if x1 is None or x1 > shift_x:
            x1 = shift_x
        if x2 is None or x2 < shift_x + layer_scaled_size:
            x2 = shift_x + layer_scaled_size
        if y1 is None or y1 > shift_y:
            y1 = shift_y
        if y2 is None or y2 < shift_y + layer_scaled_size:
            y2 = shift_y + layer_scaled_size

    if x1 and x2 and y1 and y2:
        return icon.crop((x1, y1, x2, y2))
    else:
        return icon


def get_icon_specs(a_dict: Any) -> IconSpec:
    if 'icon' in a_dict:
        layers = [{
            'icon': a_dict['icon'],
            }]
    else:
        layers = a_dict['icons']

    size = None
    if 'icon_size' in a_dict:
        size = a_dict['icon_size']
    else:
        for layer in layers:
            if 'icon_size' in layer:
                size = layer['icon_size']
                break

    if size is None:
        raise

    return IconSpec(size, layers)
