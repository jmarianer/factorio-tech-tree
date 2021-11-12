from typing import NamedTuple, TYPE_CHECKING, Any
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
    def icon(self) -> Image:
        return get_factorio_icon(self.data.reader, get_icon_specs(self.raw))


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

    @property
    def main_item(self) -> Item:
        recipe = self.raw

        if 'normal' in recipe:
            recipe = recipe['normal']

        if 'result' in recipe:
            return self.data.get_item(str(recipe['result']))
        elif 'main_product' in recipe:
            return self.data.get_item(str(recipe['main_product']))
        else:
            main_item = recipe['results'][0]
            if 'name' in main_item:
                return self.data.get_item(str(main_item['name']))
            else:
                return self.data.get_item(str(main_item[0]))

    @property
    def localized_title(self) -> str:
        try:
            if 'localised_name' in self.raw:
                return self.data.localize_array(self.raw['localised_name'])
            if f'recipe-name.{self.name}' in self.data.locale:
                return self.data.localize(f'recipe-name.{self.name}')

            return self.main_item.localized_title
        except:  # noqa
            return self.name

    @property
    def icon(self) -> Image:
        try:
            return get_factorio_icon(self.data.reader, get_icon_specs(self.raw))
        except KeyError:
            return self.main_item.icon


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
    def icon(self) -> Image:
        return get_factorio_icon(self.data.reader, get_icon_specs(self.raw))
