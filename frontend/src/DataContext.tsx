import React, { createContext, useState, useEffect, useContext } from 'react';
import { FactorioData } from './FactorioData';

const DataContext = createContext<FactorioData | null>(null);

export const DataProvider = ({ children }: { children: React.ReactNode; }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await fetch('/generated/base/data.json').then(res => res.json());
        setData(new FactorioData(data));
      } catch (err: any) {
        setError(err instanceof Error ? err : new Error('An unknown error occurred'));
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }
  if (!data) {
    return <div>No data: {error?.message}</div>;
  }

  return (
    <DataContext.Provider value={ data }>
      {children}
    </DataContext.Provider>
  );
};

export function useData() {
  const data = useContext(DataContext);
  if (!data) {
    throw new Error('DataContext not found');
  }
  return data;
}