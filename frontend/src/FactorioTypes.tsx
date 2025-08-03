import { FactorioData } from './FactorioData';
import { SUPERCLASS } from './superclass';

export class Base {
  readonly name: string;
  readonly type: string;
  readonly flags: string[];

  constructor(protected readonly data: FactorioData, public readonly json: any) {
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

  get placement_result(): Base | null {
    for (const place_result_key of ['place_result', 'placed_as_equipment_result']) {
      if (place_result_key in this.json) {
        return this.data.entities[this.json[place_result_key]];
      }
    }
    return null;
  }

  get fallback(): Base | null {
    return this.placement_result;
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

export class Turret extends Entity {
  get ammo_categories(): [string, Item[]][] {
    // TODO understand, and also fix localization
    const attack_params = this.json['attack_parameters'];
    if (attack_params['type'] === 'stream') {
      const ammo = attack_params['fluids'].map((ammo: any) => this.data.items[ammo['type']]);
      return [[this.data.localize('en', 'ammo-category-name.fluid'), ammo]];
    } else {
      let categories: string[];
      if ('ammo_type' in attack_params) {
        categories = [attack_params['ammo_type']['category']];
      } else if ('ammo_categories' in attack_params) {
        categories = attack_params['ammo_categories'];
      } else if ('ammo_category' in attack_params) {
        categories = [attack_params['ammo_category']];
      } else {
        return [];
      }

      return categories.map(category => {
        let category_name = this.data.localize('en', `ammo-category-name.${category}`);
        if (!category_name) {
          category_name = category;
        }
        const ammo: Item[] = [];
        for (const item of Object.values(this.data.items)) {
          if (item.type === 'ammo') {
            const ammo_type = item.json['ammo_type'];
            if (!Array.isArray(ammo_type)) {
              if (ammo_type['category'] === category) {
                ammo.push(item);
              }
            }
          }
        }
        return [category_name, ammo];
      });
    }
  }
}

export class CraftingMachine extends Entity {
  crafting_categories: string[];
  crafting_speed: number;

  constructor(data: FactorioData, json: any) {
    super(data, json);
    this.crafting_categories = json.crafting_categories || [];
    this.crafting_speed = json.crafting_speed || 1;
  }
}

export class MiningDrill extends Entity {
}

export class Tech extends Base {
  // ingredients: ItemWithCount[];
  prerequisites: Set<string>;
  // recipes: string[];

  constructor(data: FactorioData, json: any) {
    super(data, json);
  //   this.ingredients = rawToItemList(data, json.ingredients);
    this.prerequisites = new Set(json.prerequisites) || [];
  //   this.recipes = json.recipes.map((recipe: any) => data.recipes[recipe]);
  }
}

export class Lab extends Entity {
  researching_speed: number;
  inputs: string[];

  constructor(data: FactorioData, json: any) {
    super(data, json);
    this.researching_speed = json.researching_speed || 1;
    this.inputs = json.inputs || [];
  }
}

export class ItemWithCount {
  constructor(
    public data: FactorioData,
    public name: string,
    public min: number,
    public max: number,
    public probability: number
  ) { }

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

  get fallback(): Item | null {
    let main_item_name: string;
    if ('result' in this.json) {
      main_item_name = String(this.json.result);
    } else if ('main_product' in this.json) {
      main_item_name = String(this.json.main_product);
    } else if (this.products.length === 1) {
      main_item_name = String(this.products[0].name);
    } else {
      main_item_name = this.name;
    }
    return this.data.items[main_item_name];
  }

  get crafted_in(): [Entity, number][] {
    return this.data.get_crafting_machines_for(this.crafting_category)
      .map(([item, speed]) => [item, this.time / speed]);
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
