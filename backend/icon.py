import io
from typing import Any, Optional, NamedTuple
from PIL import Image

from mod_reader import ModReader


class RGBA(NamedTuple):
    r: float
    g: float
    b: float
    a: float = 1


class Layer(NamedTuple):
    icon_path: str
    icon_size: Optional[int] = None
    scale: float = 1
    tint: Optional[RGBA] = None
    shift: tuple[float, float] = (0, 0)


class IconSpec(NamedTuple):
    size: Optional[int]
    layers: list[Layer]


def get_factorio_icon(reader: ModReader, icon_spec: IconSpec) -> Image.Image:
    icon_size = icon_spec.size
    if icon_size is None:
        return Image.open(io.BytesIO(reader.get_binary(icon_spec.layers[0].icon_path)))

    icon = Image.new(mode='RGBA', size=(icon_size, icon_size))
    x1: Optional[float] = None
    x2: Optional[float] = None
    y1: Optional[float] = None
    y2: Optional[float] = None
    for icon_layer in icon_spec.layers:
        layer = reader.get_image(icon_layer.icon_path)

        layer_original_size = icon_layer.icon_size or icon_size
        layer_scaled_size = int(layer_original_size * icon_layer.scale)

        layer = layer \
            .crop((0, 0, layer.height, layer.height)) \
            .resize((layer_scaled_size, layer_scaled_size))

        if icon_layer.tint is not None:
            tint = icon_layer.tint

            layer_new_data = map(
                    lambda data: (
                        int(data[0] * tint.r),
                        int(data[1] * tint.g),
                        int(data[2] * tint.b),
                        int(data[3] * tint.a)),
                    layer.getdata())

            # TODO Not sure but I think the type of layer.putdata is just wrong in the stub.
            layer.putdata(list(layer_new_data))  # type: ignore

        shift_x, shift_y = icon_layer.shift
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
        return icon.crop((int(x1), int(y1), int(x2), int(y2)))
    else:
        return icon


def get_layer(a_dict: Any) -> Layer:
    tint = None
    if 'tint' in a_dict:
        a_tint = a_dict['tint']
        if isinstance(a_dict['tint'], list):
            tint = RGBA(*a_tint)
        else:
            tint = RGBA(a_tint['r'], a_tint['g'], a_tint['b'], a_tint.get('a', 1))
        if tint.r > 1 or tint.g > 1 or tint.b > 1:
            tint = RGBA(tint.r / 255, tint.g / 255, tint.b / 255, tint.a)

    return Layer(icon_path=a_dict['icon'],
                 icon_size=a_dict.get('icon_size', None),
                 scale=a_dict.get('scale', 1),
                 shift=a_dict.get('shift', (0, 0)),
                 tint=tint)


def get_icon_specs(a_dict: Any) -> IconSpec:
    if 'icon' in a_dict:
        icon = a_dict['icon']
        if isinstance(icon, str):
            layers = [Layer(icon_path=icon)]
        else:
            layers = [Layer(icon_path=icon['filename'])]
    else:
        layers = [get_layer(i) for i in a_dict['icons']]

    size = None
    if 'icon_size' in a_dict:
        size = a_dict['icon_size']
    else:
        for layer in layers:
            if layer.icon_size is not None:
                size = layer.icon_size
                break

    return IconSpec(size, layers)
