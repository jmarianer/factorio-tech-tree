import React, { createContext, useState, useEffect } from 'react';

class FactorioData {
  readonly items: Record<string, Item>;
  readonly subgroups: Record<string, Subgroup>;
  readonly groups: Record<string, Group>;

  constructor(data: any) {
    const createRecord = <T extends Base>(items: Record<string, object>, ClassType: new (data: FactorioData, item: any) => T): Record<string, T> => {
      return Object.fromEntries(
        Object.entries(items).map(([key, value]) => [key, new ClassType(this, value)])
      );
    };

    this.items = createRecord(data.item, Item);
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

class Item extends Base {
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
    return this.data.subgroups[this.json.subgroup];
  }
}

class Group extends Base {
  order: string;

  constructor(data: FactorioData, json: any) {
    super(data, json);
    this.order = json.order || '';
  }
}

class Subgroup extends Base {
  order: string;

  constructor(data: FactorioData, json: any) {
    super(data, json);
    this.order = json.order || '';
  }

  get group(): Group {
    return this.data.groups[this.json.group];
  }
}

export const DataContext = createContext<{
  data: any;
  loading: boolean;
  error: Error | null;
}>({
  data: null,
  loading: true,
  error: null,
});

export const DataProvider = ({ children }: { children: React.ReactNode; }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await fetch('/generated/base/data.json').then(res => res.json());
        console.log(data);
        setData(new FactorioData(data));
      } catch (err: any) {
        setError(err instanceof Error ? err : new Error('An unknown error occurred'));
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  return (
    <DataContext.Provider value={{ data, loading, error }}>
      {children}
    </DataContext.Provider>
  );
};
