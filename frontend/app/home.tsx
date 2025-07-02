import React from 'react';
import data from '../assets/base/data.json'

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

export default function () {
  return Dialog('All items', <>
    {Object.entries(data['item-group']).map(([key, value]) => (
      <div className="group-container" key={key}>
        <h2 className="group">
          <img src={`assets/base/icons/item-group/${key}.png`} />
          {key}
        </h2>
      </div>
    ))}
    </>,
   <>
  </>);
}
