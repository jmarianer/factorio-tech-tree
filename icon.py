from collections import namedtuple
import io
from PIL import Image, ImageOps, ImageColor


IconSpec = namedtuple('IconSpec', ['size', 'layers'])

def get_factorio_icon(reader, icon_spec):
    icon_size = icon_spec.size
    icon = Image.new(mode='RGBA', size=(icon_size, icon_size))
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
        offset = tuple(map(int, (default_offset + shift_x, default_offset + shift_y)))

        icon.alpha_composite(layer, offset)

    return icon


def get_icon_specs(a_dict):
    if 'icon' in a_dict:
        layers = [{
            'icon': a_dict['icon'],
            }]
    else:
        layers = a_dict['icons']

    if 'icon_size' in a_dict:
        size = a_dict['icon_size']
    else:
        for layer in layers:
            if 'icon_size' in layer:
                size = layer['icon_size']
                break

    return IconSpec(size, layers)
