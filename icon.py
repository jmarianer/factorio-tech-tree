from collections import namedtuple
import io
from PIL import Image, ImageOps


IconSpec = namedtuple('IconSpec', ['size', 'layers'])


def get_factorio_icon(reader, icon_spec):
    icon_size = icon_spec.size
    icon = Image.new(mode='RGBA', size=(icon_size, icon_size))
    x1 = None
    x2 = None
    y1 = None
    y2 = None
    for icon_spec in icon_spec.layers:
        layer_original_size = icon_spec.get('icon_size', icon_size)
        layer_scaled_size = int(layer_original_size * icon_spec.get('scale', 1))

        layer = Image \
            .open(io.BytesIO(reader.get_binary(icon_spec['icon']))) \
            .crop([0, 0, layer_original_size, layer_original_size]) \
            .convert('RGBA') \
            .resize((layer_scaled_size, layer_scaled_size))

        if 'tint' in icon_spec:
            tint = icon_spec['tint']
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
            layer.putdata(list(layer_new_data))

        shift_x, shift_y = icon_spec.get('shift', (0, 0))
        default_offset = (icon_size - layer_scaled_size) / 2
        shift_x += default_offset
        shift_y += default_offset
        offset = tuple(map(int, (shift_x, shift_y)))

        icon.alpha_composite(layer, offset)

        if x1 is None or x1 > shift_x:
            x1 = shift_x
        if x2 is None or x2 < shift_x + layer_scaled_size:
            x2 = shift_x + layer_scaled_size
        if y1 is None or y1 > shift_y:
            y1 = shift_y
        if y2 is None or y2 < shift_y + layer_scaled_size:
            y2 = shift_y + layer_scaled_size

    return icon.crop([x1, y1, x2, y2])


def get_icon_specs(a_dict):
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
