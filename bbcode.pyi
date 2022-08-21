from typing import Any, Callable

""" Stuff I don't use and don't have time to type
__version_info__: Any
PY3: Any
xrange = range

class CaseInsensitiveDict(MutableMapping):
    def __init__(self, data: Any | None = ..., **kwargs) -> None: ...
    def __setitem__(self, key, value) -> None: ...
    def __getitem__(self, key): ...
    def __delitem__(self, key) -> None: ...
    def __iter__(self): ...
    def __len__(self): ...
    def lower_items(self): ...
    def __eq__(self, other): ...
    def copy(self): ...

class TagOptions:
    tag_name: Any
    newline_closes: bool
    same_tag_closes: bool
    standalone: bool
    render_embedded: bool
    transform_newlines: bool
    escape_html: bool
    replace_links: bool
    replace_cosmetic: bool
    strip: bool
    swallow_trailing_newline: bool
    def __init__(self, tag_name, **kwargs) -> None: ...

g_parser: Any

def render_html(input_text, **context): ...
"""


class Parser:
    """
    TOKEN_TAG_START: int
    TOKEN_TAG_END: int
    TOKEN_NEWLINE: int
    TOKEN_DATA: int
    REPLACE_ESCAPE: Any
    REPLACE_COSMETIC: Any
    tag_opener: Any
    tag_closer: Any
    newline: Any
    recognized_tags: Any
    drop_unrecognized: Any
    escape_html: Any
    replace_cosmetic: Any
    replace_links: Any
    linker: Any
    linker_takes_context: Any
    max_tag_depth: Any
    url_template: Any
    default_context: Any
    def __init__(
            self,
            newline: str = ...,
            install_defaults: bool = ...,
            escape_html: bool = ...,
            replace_links: bool = ...,
            replace_cosmetic: bool = ...,
            tag_opener: str = ...,
            tag_closer: str = ...,
            linker: Any | None = ...,
            linker_takes_context: bool = ...,
            drop_unrecognized: bool = ...,
            default_context: Any | None = ...,
            max_tag_depth: Any | None = ...,
            url_template: str = ...
            ) -> None: ...
    def add_simple_formatter(self, tag_name, format_string, **kwargs): ...
    def install_default_formatters(self): ...
    def tokenize(self, data): ...
    def strip(self, data, strip_newlines: bool = ...): ...
    """
    def add_formatter(
            self,
            tag_name: str,
            render_func: Callable[[str, str, dict[str, str], Any, Any], str]
            ) -> None: ...

    def format(self, data: str) -> str: ...
