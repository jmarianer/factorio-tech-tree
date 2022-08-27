from __future__ import annotations
from typing import NamedTuple, TYPE_CHECKING, Any, Iterator, Optional, TypeVar, cast, Generic
from PIL.Image import Image

from icon import get_factorio_icon, get_icon_specs
if TYPE_CHECKING:
    from factorio_data import FactorioData
else:
    FactorioData = None


T = TypeVar('T')


# SUPERCLASS massaged out of https://wiki.factorio.com/Prototype_definitions
SUPERCLASS = {
        # ENTITIES
        'arrow': 'entity',
        'artillery-flare': 'entity',
        'artillery-projectile': 'entity',
        'beam': 'entity',
        'character-corpse': 'entity',
        'cliff': 'entity',
        'corpse': 'entity',
        'rail-remnants': 'corpse',
        'deconstructible-tile-proxy': 'entity',
        'entity-ghost': 'entity',
        'particle': 'entity',
        'leaf-particle': 'particle',
        'entity-with-health': 'entity',
        'entity-with-owner': 'entity-with-health',
        'accumulator': 'entity-with-owner',
        'artillery-turret': 'entity-with-owner',
        'beacon': 'entity-with-owner',
        'boiler': 'entity-with-owner',
        'burner-generator': 'entity-with-owner',
        'character': 'entity-with-owner',
        'combinator': 'entity-with-owner',
        'arithmetic-combinator': 'combinator',
        'decider-combinator': 'combinator',
        'constant-combinator': 'entity-with-owner',
        'container': 'entity-with-owner',
        'logistic-container': 'container',
        'infinity-container': 'logistic-container',
        'crafting-machine': 'entity-with-owner',
        'assembling-machine': 'crafting-machine',
        'rocket-silo': 'assembling-machine',
        'furnace': 'crafting-machine',
        'electric-energy-interface': 'entity-with-owner',
        'electric-pole': 'entity-with-owner',
        'unit-spawner': 'entity-with-owner',
        'flying-robot': 'entity-with-owner',
        'combat-robot': 'flying-robot',
        'robot-with-logistic-interface': 'flying-robot',
        'construction-robot': 'robot-with-logistic-interface',
        'logistic-robot': 'robot-with-logistic-interface',
        'gate': 'entity-with-owner',
        'generator': 'entity-with-owner',
        'heat-interface': 'entity-with-owner',
        'heat-pipe': 'entity-with-owner',
        'inserter': 'entity-with-owner',
        'lab': 'entity-with-owner',
        'lamp': 'entity-with-owner',
        'land-mine': 'entity-with-owner',
        'linked-container': 'entity-with-owner',
        'market': 'entity-with-owner',
        'mining-drill': 'entity-with-owner',
        'offshore-pump': 'entity-with-owner',
        'pipe': 'entity-with-owner',
        'infinity-pipe': 'pipe',
        'pipe-to-ground': 'entity-with-owner',
        'player-port': 'entity-with-owner',
        'power-switch': 'entity-with-owner',
        'programmable-speaker': 'entity-with-owner',
        'pump': 'entity-with-owner',
        'radar': 'entity-with-owner',
        'rail': 'entity-with-owner',
        'curved-rail': 'rail',
        'straight-rail': 'rail',
        'rail-signal-base': 'entity-with-owner',
        'rail-chain-signal': 'rail-signal-base',
        'rail-signal': 'rail-signal-base',
        'reactor': 'entity-with-owner',
        'roboport': 'entity-with-owner',
        'simple-entity-with-owner': 'entity-with-owner',
        'simple-entity-with-force': 'simple-entity-with-owner',
        'solar-panel': 'entity-with-owner',
        'storage-tank': 'entity-with-owner',
        'train-stop': 'entity-with-owner',
        'transport-belt-connectable': 'entity-with-owner',
        'linked-belt': 'transport-belt-connectable',
        'loader-1x1': 'transport-belt-connectable',
        'loader': 'transport-belt-connectable',
        'splitter': 'transport-belt-connectable',
        'transport-belt': 'transport-belt-connectable',
        'underground-belt': 'transport-belt-connectable',
        'turret': 'entity-with-owner',
        'ammo-turret': 'turret',
        'electric-turret': 'turret',
        'fluid-turret': 'turret',
        'unit': 'entity-with-owner',
        'vehicle': 'entity-with-owner',
        'car': 'vehicle',
        'rolling-stock': 'vehicle',
        'artillery-wagon': 'rolling-stock',
        'cargo-wagon': 'rolling-stock',
        'fluid-wagon': 'rolling-stock',
        'locomotive': 'rolling-stock',
        'spider-vehicle': 'vehicle',
        'wall': 'entity-with-owner',
        'fish': 'entity-with-health',
        'simple-entity': 'entity-with-health',
        'spider-leg': 'entity-with-health',
        'tree': 'entity-with-health',
        'explosion': 'entity',
        'flame-thrower-explosion': 'explosion',
        'fire': 'entity',
        'stream': 'entity',
        'flying-text': 'entity',
        'highlight-box': 'entity',
        'item-entity': 'entity',
        'item-request-proxy': 'entity',
        'particle-source': 'entity',
        'projectile': 'entity',
        'resource': 'entity',
        'rocket-silo-rocket': 'entity',
        'rocket-silo-rocket-shadow': 'entity',
        'smoke': 'smoke',
        'smoke-with-trigger': 'smoke',
        'speech-bubble': 'entity',
        'sticker': 'entity',
        'tile-ghost': 'entity',

        # EQUIPMENT
        'active-defense-equipment': 'equipment',
        'battery-equipment': 'equipment',
        'belt-immunity-equipment': 'equipment',
        'energy-shield-equipment': 'equipment',
        'generator-equipment': 'equipment',
        'movement-bonus-equipment': 'equipment',
        'night-vision-equipment': 'equipment',
        'roboport-equipment': 'equipment',
        'solar-panel-equipment': 'equipment',

        # ITEMS
        'ammo': 'item',
        'capsule': 'item',
        'gun': 'item',
        'item-with-entity-data': 'item',
        'item-with-label': 'item',
        'item-with-inventory': 'item-with-label',
        'blueprint-book': 'item-with-inventory',
        'item-with-tags': 'item-with-label',
        'selection-tool': 'item-with-label',
        'blueprint': 'selection-tool',
        'copy-paste-tool': 'selection-tool',
        'deconstruction-item': 'selection-tool',
        'upgrade-item': 'selection-tool',
        'module': 'item',
        'rail-planner': 'item',
        'spidertron-remote': 'item',
        'tool': 'item',
        'armor': 'tool',
        'mining-tool': 'tool',
        'repair-tool': 'tool',

        # Not true according to the Factorio docs but will do for our purposes (for now):
        'equipment': 'entity',
        'fluid': 'item',
}


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
        # Try localization in data
        if 'localised_name' in self.raw:
            return self.data.localize_array(self.raw['localised_name'])

        # Try localization in locale, based on type
        cur_type: Optional[str] = self.type
        while cur_type:
            maybe_ret = self.data.localize(f'{cur_type}-name.{self.name}')
            if maybe_ret:
                return maybe_ret
            cur_type = SUPERCLASS.get(cur_type)

        # Try fallback object
        fallback = self.fallback()
        if fallback:
            return fallback.localized_title

        # As a last resort, return the unadorned name. TODO put a breakpoint here and see where this happens.
        return self.name

    @property
    def description(self) -> str:
        # Try localization in data
        if 'localised_description' in self.raw:
            return self.data.localize_array(self.raw['localised_description'])

        # Try localization in locale, based on type
        cur_type: Optional[str] = self.type
        while cur_type:
            maybe_ret = self.data.localize(f'{cur_type}-description.{self.name}')
            if maybe_ret:
                return maybe_ret
            cur_type = SUPERCLASS.get(cur_type)

        # Try fallback object
        fallback = self.fallback()
        if fallback:
            return fallback.description

        return ''

    @property
    def icon(self) -> Image:
        try:
            return get_factorio_icon(self.data.reader, get_icon_specs(self.raw))
        except KeyError:
            fallback = self.fallback()
            if fallback:
                return fallback.icon
            else:
                raise

    def fallback(self) -> Optional[Base]:
        return None

    def __str__(self) -> str:
        return f'{self.type}.{self.name}'


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

    def fallback(self) -> Optional[Entity]:
        for place_result_key in ('place_result', 'placed_as_equipment_result'):
            if place_result_key in self.raw:
                return self.data.entities.get(self.raw[place_result_key])
        return None

    @property
    def subgroup(self) -> Subgroup:
        return self.data.subgroups[self.raw['subgroup']]


class ItemWithCount(NamedTuple):
    data: FactorioData
    name: str
    amount: int

    @property
    def item(self) -> Item:
        return self.data.items[self.name]

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

    def fallback(self) -> Optional[Item]:
        if 'result' in self.raw:
            main_item_name = str(self.raw['result'])
        elif 'main_product' in self.raw:
            main_item_name = str(self.raw['main_product'])
        elif len(self.products) == 1:
            main_item_name = str(self.products[0].name)
        else:
            main_item_name = self.name
        return self.data.items.get(main_item_name)

    @property
    def crafted_in(self) -> list[tuple[Entity, float]]:
        return [(item, self.time / speed)
                for item, speed in self.data.get_crafting_machines_for(self.crafting_category)]

    @property
    def subgroup(self) -> Subgroup:
        if 'subgroup' in self.raw:
            return self.data.subgroups[self.raw['subgroup']]
        else:
            fallback = self.fallback()
            if fallback:
                return fallback.subgroup
            else:
                raise

    @property
    def order(self) -> str:
        if 'order' in self.raw:
            return cast(str, self.raw['order'])
        else:
            fallback = self.fallback()
            if fallback:
                return fallback.order
            else:
                return ''


class Entity(Base):
    pass


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

    def fallback(self) -> Item:
        return self.data.items.get(
                self.name,
                Item(self.data, dict(name=self.name, type='item')))


class Group(Base):
    order = JsonProp[str]()


class Subgroup(Base):
    order = JsonProp[str]()

    @property
    def group(self) -> Group:
        return self.data.groups[self.raw['group']]
