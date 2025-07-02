import React, { createContext, useState, useEffect } from 'react';

export const DataContext = createContext<{
  data: any;
  loading: boolean;
  error: string | null;
}>({
  data: null,
  loading: true,
  error: null,
});

export const DataProvider = ({ children }: { children: React.ReactNode; }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetch('/generated/base/data.json').then(res => res.json());
        setData(data);
      } catch (err: any) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
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
