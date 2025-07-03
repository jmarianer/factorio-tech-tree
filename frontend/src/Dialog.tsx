import React from 'react';

export function Dialog(title: string, header: React.ReactNode, content: React.ReactNode): React.ReactElement {
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
