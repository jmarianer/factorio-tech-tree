from __future__ import annotations
from typing import NamedTuple, TYPE_CHECKING, Any, Iterator
from PIL.Image import Image

from icon import get_factorio_icon, get_icon_specs
if TYPE_CHECKING:
    from factorio_data import FactorioData
else:
    FactorioData = None


class Item(NamedTuple):
    data: FactorioData
    raw: Any
    name: str
    type: str

    @property
    def localized_title(self) -> str:
        try:
            if 'localised_name' in self.raw:
                return self.data.localize_array(self.raw['localised_name'])
            elif f'{self.type}-name.{self.name}' in self.data.locale:
                return self.data.localize(f'{self.type}-name.{self.name}')
            else:
                return self.data.localize(f'entity-name.{self.name}')
        except:  # noqa
            return self.name

    @property
    def description(self) -> str:
        try:
            if 'localised_description' in self.raw:
                return self.data.localize_array(self.raw['localised_description'])
            elif f'{self.type}-description.{self.name}' in self.data.locale:
                return self.data.localize(f'{self.type}-description.{self.name}')
            else:
                return self.data.localize(f'entity-description.{self.name}')
        except:  # noqa
            return ''

    @property
    def icon(self) -> Image:
        return get_factorio_icon(self.data.reader, get_icon_specs(self.raw))

    @property
    def used_in(self) -> Iterator[Recipe]:
        return (r
                for _, r in sorted(self.data.recipes.items())
                if self.name in (i.name for i in r.ingredients))

    @property
    def produced_in(self) -> Iterator[Recipe]:
        return (r
                for _, r in sorted(self.data.recipes.items())
                if self.name in (p.name for p in r.products))


class ItemWithCount(NamedTuple):
    data: FactorioData
    name: str
    amount: int

    @property
    def item(self) -> Item:
        return self.data.get_item(self.name)

    @property
    def localized_title(self) -> str:
        return self.item.localized_title


class Recipe(NamedTuple):
    data: FactorioData
    raw: Any
    name: str
    ingredients: list[ItemWithCount]
    products: list[ItemWithCount]
    time: int
    crafting_category: str

    @property
    def _main_item(self) -> Item:
        if 'result' in self.raw:
            return self.data.get_item(str(self.raw['result']))
        elif 'main_product' in self.raw:
            return self.data.get_item(str(self.raw['main_product']))
        else:
            main_item = self.raw['results'][0]
            if 'name' in main_item:
                return self.data.get_item(str(main_item['name']))
            else:
                return self.data.get_item(str(main_item[0]))

    @property
    def localized_title(self) -> str:
        try:
            if 'localised_name' in self.raw:
                return self.data.localize_array(self.raw['localised_name'])
            elif f'recipe-name.{self.name}' in self.data.locale:
                return self.data.localize(f'recipe-name.{self.name}')
            else:
                return self._main_item.localized_title
        except:  # noqa
            return self.name

    @property
    def description(self) -> str:
        try:
            if 'localised_description' in self.raw:
                return self.data.localize_array(self.raw['localised_description'])
            elif f'recipe-description.{self.name}' in self.data.locale:
                return self.data.localize(f'recipe-description.{self.name}')
            else:
                return self._main_item.description
        except:  # noqa
            return ''

    @property
    def icon(self) -> Image:
        try:
            return get_factorio_icon(self.data.reader, get_icon_specs(self.raw))
        except KeyError:
            return self._main_item.icon

    @property
    def crafted_in(self) -> list[tuple[Item, float]]:
        return [(item, self.time / speed)
                for item, speed in self.data.get_crafting_machines_for(self.crafting_category)]


class Tech(NamedTuple):
    data: FactorioData
    raw: Any
    name: str
    time: int
    prerequisite_names: set[str]
    ingredients: list[ItemWithCount]
    recipes: list[Recipe]

    @property
    def localized_title(self) -> str:
        try:
            if 'localised_name' in self.raw:
                return self.data.localize_array(self.raw['localised_name'])
            else:
                return self.data.localize(f'technology-name.{self.name}')
        except:  # noqa
            return self.name

    @property
    def description(self) -> str:
        try:
            if 'localised_description' in self.raw:
                return self.data.localize_array(self.raw['localised_description'])
            else:
                return self.data.localize(f'technology-description.{self.name}')
        except:  # noqa
            return ''

    @property
    def icon(self) -> Image:
        return get_factorio_icon(self.data.reader, get_icon_specs(self.raw))
