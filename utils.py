import base64
import io
import lupa


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
