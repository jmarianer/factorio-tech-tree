from typing import Any

import bbcode
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

def font(_tag_name: str, value: str, options: dict[str, str], _parent: Any, _context: Any) -> str:
    if options['font'] == 'default-bold':
        return f'<b>{value}</b>'
    if options['font'] == 'default-semibold':
        return f'<b>{value}</b>'
    if options['font'] == 'default-tiny-bold':
        return f'<b>{value}</b>'
    raise


def get_jinja_environment():
    parser = bbcode.Parser()
    parser.add_formatter('font', font)

    def render_localized_text(text: str) -> Markup:
        return Markup(parser.format(text.replace('\\n', '\n')))

    env = Environment(loader=FileSystemLoader('.'), autoescape=True)
    env.filters['bbcode'] = render_localized_text

    return env
