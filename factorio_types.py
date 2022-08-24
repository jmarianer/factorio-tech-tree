from __future__ import annotations
from typing import NamedTuple, TYPE_CHECKING, Any, Iterator, Optional, TypeVar, cast, Generic
from PIL.Image import Image

from icon import get_factorio_icon, get_icon_specs
if TYPE_CHECKING:
    from factorio_data import FactorioData
else:
    FactorioData = None


T = TypeVar('T')


class JsonProp(Generic[T]):
    default: Optional[T]

    def __init__(self, default: Optional[T] = None):
        self.default = default

    def __set_name__(self, _owner: Any, name: str) -> None:
        self.name = name

    def __get__(self, obj: Any, obj_type: Any = None) -> T:
        if self.default is None:
            return cast(T, obj.raw[self.name])
        else:
            return cast(T, obj.raw.get(self.name, self.default))


class Base:
    data: FactorioData
    raw: Any

    name = JsonProp[str]()
    type = JsonProp[str]()

    def __init__(self, data: FactorioData, raw: Any):
        self.data = data
        self.raw = raw

    @property
    def localized_title(self) -> str:
        try:
            if 'localised_name' in self.raw:
                return self.data.localize_array(self.raw['localised_name'])
            else:
                return self.data.localize(f'{self.type}-name.{self.name}')
        except:  # noqa
            return self.name

    @property
    def description(self) -> str:
        try:
            if 'localised_description' in self.raw:
                return self.data.localize_array(self.raw['localised_description'])
            else:
                return self.data.localize(f'{self.type}-description.{self.name}')
        except:  # noqa
            return ''

    @property
    def icon(self) -> Image:
        return get_factorio_icon(self.data.reader, get_icon_specs(self.raw))


class Item(Base):
    order = JsonProp[str]()

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
        data = self.data
        return data.items[self.name]

    @property
    def localized_title(self) -> str:
        return self.item.localized_title


def _raw_to_item_list(data: FactorioData, raw_items: list[Any]) -> Iterator[ItemWithCount]:
    for raw_item in raw_items:
        if isinstance(raw_item, dict):
            name = raw_item['name']
            if 'amount' in raw_item:
                amount = raw_item['amount']
            else:
                amount = f'{raw_item["amount_min"]}–{raw_item["amount_max"]}'
        else:
            name, amount = raw_item
        yield ItemWithCount(data, name, amount)


class Recipe(Base):
    ingredients: list[ItemWithCount]
    products: list[ItemWithCount]
    time: int
    crafting_category: str

    name = JsonProp[str]()
    type = JsonProp[str]()
    hidden = JsonProp[bool](False)

    def __init__(self, data: FactorioData, raw: Any):
        super().__init__(data, raw)

        if 'normal' in self.raw:
            self.raw.update(self.raw['normal'])

        if 'results' in self.raw:
            results = self.raw['results']
        else:
            results = [[self.raw['result'], 1]]

        self.ingredients = list(_raw_to_item_list(self.data, self.raw['ingredients']))
        self.products = list(_raw_to_item_list(self.data, results))
        self.time = self.raw.get('energy_required', 0.5)
        self.crafting_category = self.raw.get('category', 'crafting')

    @property
    def _main_item(self) -> Optional[Item]:
        if 'result' in self.raw:
            item_name = str(self.raw['result'])
            return self.data.items[item_name]
        elif 'main_product' in self.raw:
            item_name = str(self.raw['main_product'])
            return self.data.items[item_name]
        elif len(self.products) == 1:
            item_name = str(self.products[0].name)
            return self.data.items[item_name]
        else:
            return None

    @property
    def localized_title(self) -> str:
        try:
            if 'localised_name' in self.raw:
                return self.data.localize_array(self.raw['localised_name'])
            elif f'recipe-name.{self.name}' in self.data.locale:
                return self.data.localize(f'recipe-name.{self.name}')
            elif self._main_item:
                return self._main_item.localized_title
        except:  # noqa
            pass
        return self.name

    @property
    def description(self) -> str:
        try:
            if 'localised_description' in self.raw:
                return self.data.localize_array(self.raw['localised_description'])
            elif f'recipe-description.{self.name}' in self.data.locale:
                return self.data.localize(f'recipe-description.{self.name}')
            elif self._main_item:
                return self._main_item.description
        except:  # noqa
            pass
        return ''

    @property
    def icon(self) -> Image:
        try:
            return get_factorio_icon(self.data.reader, get_icon_specs(self.raw))
        except KeyError:
            if self._main_item:
                return self._main_item.icon
            else:
                raise

    @property
    def crafted_in(self) -> list[tuple[Item, float]]:
        return [(item, self.time / speed)
                for item, speed in self.data.get_crafting_machines_for(self.crafting_category)]

    @property
    def order(self) -> str:
        if 'order' in self.raw:
            return cast(str, self.raw['order'])
        elif self._main_item:
            return self._main_item.order
        else:
            return ''


class Tech(Base):
    time: int
    prerequisite_names: set[str]
    ingredients: list[ItemWithCount]
    recipes: list[Recipe]
    name = JsonProp[str]()
    type = JsonProp[str]()
    enabled = JsonProp[bool](default=True)

    def __init__(self, data: FactorioData, raw: Any):
        super().__init__(data, raw)

        count = self.raw['unit']['count']
        ingredients = [
            ItemWithCount(self.data, i.name, i.amount * count)
            for i in _raw_to_item_list(self.data, self.raw['unit']['ingredients'])]
        self.time = int(self.raw['unit']['time']) * int(count)
        self.prerequisite_names = set(self.raw.get('prerequisites', []))
        self.ingredients = ingredients
        factorio_data = self.data
        self.recipes = [factorio_data.recipes[effect['recipe']]
                        for effect in self.raw.get('effects', [])
                        if 'recipe' in effect]
