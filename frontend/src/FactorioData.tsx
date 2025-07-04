import { all_entities, all_items } from './superclass';
import { SUPERCLASS } from './superclass';

export class FactorioData {
  readonly items: Record<string, Item>;
  readonly subgroups: Record<string, Subgroup>;
  readonly groups: Record<string, Group>;
  readonly entities: Record<string, Entity>;
  readonly locale: Record<string, any>;
  readonly recipes: Record<string, Recipe>;

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
    this.entities = createRecord(
      all_entities
        .reduce((acc, entityType) => ({ ...acc, ...data['raw'][entityType] }), {}),
      Entity
    );
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
    // Helper for replacing __n__ with localized value

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
}

class Base {
  readonly name: string;
  readonly type: string;
  readonly flags: string[];

  constructor(protected data: FactorioData, protected json: any) {
    this.name = json.name || '';
    this.type = json.type || '';
    this.flags = json.flags || [];
  }
  get fallback(): Base | null {
    return null;
  }

  localize(language: string, raw_field: string, locale_field: string): string | undefined {
    // Try localization in data
    if (this.json[raw_field]) {
      return this.data.localizeArray(language, this.json[raw_field]);
    }

    // Try localization in locale, based on type
    let cur_type: string | undefined = this.type;
    while (cur_type) {
      const maybe_ret = this.data.localize(language, `${cur_type}-${locale_field}.${this.name}`);
      if (maybe_ret) {
        return maybe_ret;
      }
      cur_type = SUPERCLASS[cur_type];
    }

    // Try fallback object
    const fallback = this.fallback;
    if (fallback) {
      return fallback.localize(language, raw_field, locale_field);
    }
  }

  localized_title(language: string): string {
    return this.localize(language, 'localised_name', 'name') || this.name;
  }

  description(language: string): string {
    return this.localize(language, 'localised_description', 'description') || '';
  }
}

export class Item extends Base {
  order: string;
  hidden: boolean;

  constructor(data: FactorioData, json: any) {
    super(data, json);
    this.order = json.order || '';
    this.hidden = json.hidden || false;
  }

  get used_in(): Recipe[] {
    return Object.values(this.data.recipes)
      .filter(r => r.ingredients.some(i => i.name === this.name))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  get produced_in(): Recipe[] {
    return Object.values(this.data.recipes)
      .filter(r => r.products.some(p => p.name === this.name))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  get fallback(): Base | null {
    for (const place_result_key of ['place_result', 'placed_as_equipment_result']) {
      if (place_result_key in this.json) {
        return this.data.entities[this.json[place_result_key]];
      }
    }
    return null;
  }

  get subgroup(): Subgroup {
    if (this.type === 'fluid') {
      return this.data.subgroups['fluid'];
    }
    return this.data.subgroups[this.json.subgroup];
  }
}

export class Entity extends Base {
}


export class ItemWithCount {
  constructor(
    public data: FactorioData,
    public name: string,
    public min: number,
    public max: number,
    public probability: number
  ) {}

  get item(): Item {
    return this.data.items[this.name];
  }

  localized_title(language: string): string {
    return this.item.localized_title(language);
  }

  get quantity(): string {
    /**
     * Returns the quantity as a string of the form
     * [min[–max]x][probability%]
     */
    let amount: string;
    if (this.min < this.max) {
      amount = `${this.min}–${this.max}`;
    } else {
      amount = this.min.toString();
    }
    amount += 'x';

    let prob: string;
    if (this.probability === 1) {
      prob = '';
    } else {
      prob = (this.probability * 100).toFixed(2) + '%';
    }

    if (this.min === 1 && this.max === 1 && prob) {
      return prob;
    } else {
      return `${prob} ${amount}`;
    }
  }
}

function rawToItemList(data: FactorioData, raw_items: any[]): ItemWithCount[] {
  const result: ItemWithCount[] = [];

  for (const raw_item of raw_items) {
    let min_amount: number;
    let max_amount: number;
    let probability: number;
    let name: string;

    if (Array.isArray(raw_item)) {
      [name, min_amount] = raw_item;
      max_amount = min_amount;
      probability = 1;
    } else {
      name = raw_item.name;
      if ('amount' in raw_item) {
        min_amount = max_amount = raw_item.amount;
      } else {
        min_amount = raw_item.amount_min;
        max_amount = raw_item.amount_max;
      }
      if ('probability' in raw_item) {
        probability = Number(raw_item.probability);
      } else {
        probability = 1;
      }
    }
    result.push(new ItemWithCount(data, name, min_amount, max_amount, probability));
  }

  return result;
}

export class Recipe extends Base {
  hidden: boolean;
  ingredients: ItemWithCount[];
  products: ItemWithCount[];
  time: number;
  crafting_category: string;

  constructor(data: FactorioData, json: any) {
    if (json.name === 'express-transport-belt') {
      console.log(json);
    }
    if ('normal' in json) {
      Object.assign(json, json.normal);
    }
    super(data, json);

    const results: any[] = 'results' in json ? json.results : [[json.result, 1]];

    this.ingredients = rawToItemList(data, json.ingredients);
    this.products = rawToItemList(data, results);
    this.time = json.energy_required || 0.5;
    this.crafting_category = json.category || 'crafting';
    this.hidden = json.hidden || false;
  }
} 

export class Group extends Base {
  order: string;

  constructor(data: FactorioData, json: any) {
    super(data, json);
    this.order = json.order || '';
  }
}

export class Subgroup extends Base {
  order: string;

  constructor(data: FactorioData, json: any) {
    super(data, json);
    this.order = json.order || '';
  }

  get group(): Group {
    return this.data.groups[this.json.group];
  }
}
