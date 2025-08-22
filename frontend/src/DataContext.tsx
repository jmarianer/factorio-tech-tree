import React, { createContext, useState, useEffect, useContext } from 'react';
import { useParams } from 'react-router-dom';

const DataContext = createContext<any>(null);

export function DataProvider({ path, children, fn }: { path: string; children: React.ReactNode; fn?: (foo: any) => any }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      const data = await fetch(path).then(res => res.json());
      if (fn) {
        setData(fn(data));
      } else {
        setData(data);
      }
      setLoading(false);
    };

    loadData();
  }, [path]);

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

export function useData<T>() {
  const data = useContext(DataContext);
  if (!data) {
    throw new Error('DataContext not found');
  }
  return data as unknown as T;
}