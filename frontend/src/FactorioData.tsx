import { Entity, Item, Subgroup, Group, Recipe, Base, CraftingMachine, Turret } from './FactorioTypes';
import { all_items } from './superclass';
import _ from 'lodash';

const all_entities = {
  'arrow': Entity,
  'artillery-flare': Entity,
  'artillery-projectile': Entity,
  'beam': Entity,
  'character-corpse': Entity,
  'cliff': Entity,
  'corpse': Entity,
  'rail-remnants': Entity,
  'deconstructible-tile-proxy': Entity,
  'entity-ghost': Entity,
  'particle': Entity,
  'leaf-particle': Entity,
  'entity-with-health': Entity,
  'entity-with-owner': Entity,
  'accumulator': Entity,
  'artillery-turret': Entity,
  'beacon': Entity,
  'boiler': Entity,
  'burner-generator': Entity,
  'character': Entity,
  'combinator': Entity,
  'arithmetic-combinator': Entity,
  'decider-combinator': Entity,
  'constant-combinator': Entity,
  'container': Entity,
  'logistic-container': Entity,
  'infinity-container': Entity,
  'crafting-machine': CraftingMachine,
  'assembling-machine': CraftingMachine,
  'rocket-silo': CraftingMachine,
  'furnace': CraftingMachine,
  'electric-energy-interface': Entity,
  'electric-pole': Entity,
  'unit-spawner': Entity,
  'flying-robot': Entity,
  'combat-robot': Entity,
  'robot-with-logistic-interface': Entity,
  'construction-robot': Entity,
  'logistic-robot': Entity,
  'gate': Entity,
  'generator': Entity,
  'heat-interface': Entity,
  'heat-pipe': Entity,
  'inserter': Entity,
  'lab': Entity,
  'lamp': Entity,
  'land-mine': Entity,
  'linked-container': Entity,
  'market': Entity,
  'mining-drill': Entity,
  'offshore-pump': Entity,
  'pipe': Entity,
  'infinity-pipe': Entity,
  'pipe-to-ground': Entity,
  'player-port': Entity,
  'power-switch': Entity,
  'programmable-speaker': Entity,
  'pump': Entity,
  'radar': Entity,
  'rail': Entity,
  'curved-rail': Entity,
  'straight-rail': Entity,
  'rail-signal-base': Entity,
  'rail-chain-signal': Entity,
  'rail-signal': Entity,
  'reactor': Entity,
  'roboport': Entity,
  'simple-entity-with-owner': Entity,
  'simple-entity-with-force': Entity,
  'solar-panel': Entity,
  'storage-tank': Entity,
  'train-stop': Entity,
  'transport-belt-connectable': Entity,
  'linked-belt': Entity,
  'loader-1x1': Entity,
  'loader': Entity,
  'splitter': Entity,
  'transport-belt': Entity,
  'underground-belt': Entity,
  'turret': Turret,
  'ammo-turret': Turret,
  'electric-turret': Turret,
  'fluid-turret': Turret,
  'unit': Entity,
  'vehicle': Entity,
  'car': Entity,
  'rolling-stock': Entity,
  'artillery-wagon': Entity,
  'cargo-wagon': Entity,
  'fluid-wagon': Entity,
  'locomotive': Entity,
  'spider-vehicle': Entity,
  'wall': Entity,
  'fish': Entity,
  'simple-entity': Entity,
  'spider-leg': Entity,
  'tree': Entity,
  'explosion': Entity,
  'flame-thrower-explosion': Entity,
  'fire': Entity,
  'stream': Entity,
  'flying-text': Entity,
  'highlight-box': Entity,
  'item-entity': Entity,
  'item-request-proxy': Entity,
  'particle-source': Entity,
  'projectile': Entity,
  'resource': Entity,
  'rocket-silo-rocket': Entity,
  'rocket-silo-rocket-shadow': Entity,
  'smoke': Entity,
  'smoke-with-trigger': Entity,
  'speech-bubble': Entity,
  'sticker': Entity,
  'tile-ghost': Entity,
}

export class FactorioData {
  readonly items: Record<string, Item>;
  readonly subgroups: Record<string, Subgroup>;
  readonly groups: Record<string, Group>;
  readonly entities: Record<string, Entity>;
  readonly locale: Record<string, any>;
  readonly recipes: Record<string, Recipe>;
  readonly character = new Entity(this, {
    name: 'character',
    type: 'character',
    flags: [],
    json: {
      crafting_categories: ['crafting'],
      crafting_speed: 1,
    },
  });

  constructor(data: any) {
    const createRecord = <T extends Base>(items: Record<string, object>, ClassType: new (data: FactorioData, item: any) => T): Record<string, T> => {
      return Object.fromEntries(
        Object.entries(items).map(([key, value]) => [key, new ClassType(this, value)])
      );
    };

    this.items = createRecord(
      all_items
        .reduce((acc, itemType) => ({ ...acc, ...data['raw'][itemType] }), {}),
      Item
    );
    this.entities = _(all_entities)
      .toPairs()
      .map(([entityType, ClassType]) => createRecord(data['raw'][entityType] || {}, ClassType))
      .reduce((acc, record) => ({ ...acc, ...record }), {});
    this.subgroups = createRecord(data['raw']['item-subgroup'], Subgroup);
    this.groups = createRecord(data['raw']['item-group'], Group);
    this.recipes = createRecord(data['raw']['recipe'], Recipe);
    this.locale = data['locale'];
  }

  localize(language: string, name: string): string {
    const locale = this.locale[language];
    let localized: string = '';
    if (name in locale) {
      localized = locale[name];
    } else {
      const match = name.match(/(.*)-(\d+)$/);
      if (!match || !(locale && match[1] in locale)) {
        // XXX This is a horrible kludge
        return '';
      }
      localized = locale[match[1]] + ' ' + match[2];
    }

    // Replace __ENTITY__foo__ or __ITEM__bar__ with localized names
    localized = localized.replace(/__ENTITY__([^_]*)__/, (_, name) => this.localize(language, `entity-name.${name}`));
    localized = localized.replace(/__ITEM__([^_]*)__/, (_, name) => this.localize(language, `item-name.${name}`));

    return localized;
  }

  localizeArray(language: string, array: string | number | string[]): string {
    if (typeof array === 'string') {
      return array;
    } else if (typeof array === 'number') {
      return String(array);
    } else if (!array[0]) {
      return array.map((x: any) => this.localizeArray(language, x)).join('');
    } else {
      // Replace __n__ with localized value from array[n]
      return this.localize(language, array[0]).replace(/__(\d+)__/g, ((_, n) => {
          return this.localizeArray(language, array[parseInt(n, 10)]);
        }));
    }
  }

  get_crafting_machines_for(crafting_category: string): [Entity, number][] {
    const result: [Entity, number][] = [];

    if (crafting_category === 'crafting') {
      result.push([this.character, 1]);
    }

    for (const machine of Object.values(this.entities)) {
      if (machine instanceof CraftingMachine && machine.crafting_categories.includes(crafting_category)) {
        result.push([machine, machine.crafting_speed]);
      }
    }

    return result;
  }
}
