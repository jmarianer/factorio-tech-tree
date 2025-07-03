import { all_items } from './superclass';

export class FactorioData {
  readonly items: Record<string, Item>;
  readonly subgroups: Record<string, Subgroup>;
  readonly groups: Record<string, Group>;

  constructor(data: any) {
    const createRecord = <T extends Base>(items: Record<string, object>, ClassType: new (data: FactorioData, item: any) => T): Record<string, T> => {
      return Object.fromEntries(
        Object.entries(items).map(([key, value]) => [key, new ClassType(this, value)])
      );
    };

    this.items = createRecord(
      all_items
        .reduce((acc, itemType) => ({ ...acc, ...data[itemType] }), {}),
      Item
    );
    this.subgroups = createRecord(data['item-subgroup'], Subgroup);
    this.groups = createRecord(data['item-group'], Group);
  }
}

abstract class Base {
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
}

export class Item extends Base {
  order: string;
  hidden: boolean;

  constructor(data: FactorioData, json: any) {
    super(data, json);
    this.order = json.order || '';
    this.hidden = json.hidden || false;
  }

  get fallback() {
    return null;
  }

  get subgroup(): Subgroup {
    if (this.type === 'fluid') {
      return this.data.subgroups['fluid'];
    }
    return this.data.subgroups[this.json.subgroup];
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
