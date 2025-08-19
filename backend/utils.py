import base64
import io
import re
from lupa.lua52 import LuaRuntime
from typing import Any
from PIL.Image import Image
from pathlib import Path
from icon import get_factorio_icon, get_icon_specs
from mod_reader import ModReader
from animation import get_animation, get_animation_specs
import math

# TODO: Figure out if this can be done more elegantly
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lupa.lua52 import LuaObject
else:
    LuaObject = int


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


def lua_table_to_python(obj: LuaObject) -> Any:
    if isinstance(obj, int) or isinstance(obj, str) or isinstance(obj, float) or isinstance(obj, bool) or obj is None:
        return obj
    else:
        if all(isinstance(i, int) for i in obj.keys()):
            return [lua_table_to_python(v) for v in obj.values()]
        else:
            return {str(k): lua_table_to_python(v) for k, v in obj.items()}


def python_to_lua_table(lua: LuaRuntime, obj: Any) -> LuaObject:
    if isinstance(obj, dict):
        return lua.table(**{
            k: python_to_lua_table(lua, v)
            for k, v in obj.items()})
    elif isinstance(obj, list):
        return lua.table(*[
            python_to_lua_table(lua, v)
            for v in obj])
    elif isinstance(obj, int) or isinstance(obj, str) or isinstance(obj, bool) or isinstance(obj, float) or obj is None:
        return obj
    else:
        raise


def image_to_data_url(image: Image) -> str:
    stream = io.BytesIO()
    image.save(stream, 'png')
    encoded = base64.b64encode(stream.getvalue()).decode('ascii')
    return 'data:image/jpeg;base64,' + encoded


def parse_dependencies(dependency_spec: str) -> tuple[str, str, str]:
    # ! for incompatibility
    # ? for an optional dependency
    # (?) for a hidden optional dependency
    # ~ for a dependency that does not affect load order
    # or no prefix for a hard requirement for the other mod.
    match = re.match(r'^(?P<prefix>!|\?|\(\?\)|~)? \s* (?P<mod>.+?) \s* (?P<rest>[=>].*)?$',
                     dependency_spec, re.VERBOSE)
    if match:
        return match['prefix'], match['mod'], match['rest']
    else:
        raise


def write_icon(filename: Path, object: Any, data_reader: ModReader) -> None:
    icon_spec = get_icon_specs(object)
    icon = get_factorio_icon(data_reader, icon_spec)
    icon.save(filename)


def write_animation(filename: Path, animation_data: Any, data_reader: ModReader) -> None:
    animation_spec = get_animation_specs(animation_data)
    animation = get_animation(data_reader, animation_spec)
    image_iter = iter(animation)
    first_image = next(image_iter)
    first_image.save(filename, save_all=True, append_images=image_iter, optimize=True)