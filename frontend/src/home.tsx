import React, { useContext } from 'react';
import { DataContext } from './DataContext';

function Dialog(title: string, header: React.ReactNode, content: React.ReactNode): React.ReactElement {
  return <div className="main-dialog">
    <h1>{title}</h1>
    <div className="dialog-wrapper">
        <div className="dialog-header">
            {header}
        </div>
        <div className="dialog-content">
            {content}
        </div>
    </div>
  </div>;
}

export default function Home() {
  const { data, loading, error } = useContext(DataContext);
  if (loading) {
    return <div>Loading...</div>;
  }
  if (!data) {
    return <div>No data: {error?.message}</div>;
  }

  return Dialog('All items', <>
    {Object.entries(data.groups).map(([key, value]) => (
      <div className="group-container" key={key}>
        <h2 className="group">
          <img src={`generated/base/icons/item-group/${key}.png`} alt={key} />
          {key}
        </h2>
      </div>
    ))}
  </>,
    <> </>);
}
