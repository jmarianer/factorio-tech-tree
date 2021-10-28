import base64
import io
import lupa
import re


def lua_table_to_python(obj):
    if lupa.lua_type(obj) == 'table':
        if all(isinstance(i, int) for i in obj.keys()):
            return [lua_table_to_python(v) for v in obj.values()]
        else:
            return {str(k): lua_table_to_python(v) for k, v in obj.items()}
    elif lupa.lua_type(obj) is not None:
        return lupa.lua_type(obj)
    else:
        return obj


def python_to_lua_table(lua, obj):
    if isinstance(obj, dict):
        return lua.table(**{
            k: python_to_lua_table(lua, v)
            for k, v in obj.items()})
    else:
        return obj


def image_to_data_url(image):
    stream = io.BytesIO()
    image.save(stream, 'png')
    encoded = base64.b64encode(stream.getvalue()).decode('ascii')
    return 'data:image/jpeg;base64,' + encoded


def parse_dependencies(dependency_spec):
    # ! for incompatibility
    # ? for an optional dependency
    # (?) for a hidden optional dependency
    # ~ for a dependency that does not affect load order
    # or no prefix for a hard requirement for the other mod.
    match = re.match('^(?P<prefix>!|\?|\(\?\)|~)? \s* (?P<mod>[^ ]+) (?P<rest>.*)$', dependency_spec, re.VERBOSE)
    return match['prefix'], match['mod'], match['rest']

