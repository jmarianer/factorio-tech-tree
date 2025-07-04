import React, { createContext, useState, useEffect, useContext } from 'react';
import { FactorioData } from './FactorioData';
import { useParams } from 'react-router-dom';

const DataContext = createContext<FactorioData | null>(null);

export const DataProvider = ({ children }: { children: React.ReactNode; }) => {
  const { regime } = useParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      const data = await fetch(`/generated/${regime}/data.json`).then(res => res.json());
      setData(new FactorioData(data));
      setLoading(false);
    };

    loadData();
  }, [regime]);

  if (loading) {
    return <div>Loading...</div>;
  }
  if (!data) {
    return <div>No data?!</div>;
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