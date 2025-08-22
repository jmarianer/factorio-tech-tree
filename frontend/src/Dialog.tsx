import React, { ReactElement, ReactNode } from 'react';

export function DialogHeader({ children }: { children: ReactNode }) {
  return <div className="dialog-header">{children}</div>;
}

interface DialogProps {
  title: string;
  children: ReactNode;
}

export function Dialog({ title, children }: DialogProps): ReactElement {
  let header: ReactNode = null;
  const content: ReactNode[] = [];

  React.Children.forEach(children, child => {
    if (
      React.isValidElement(child) &&
      child.type === DialogHeader
    ) {
      header = child;
    } else if (child !== null && child !== undefined) {
      content.push(child);
    }
  });

  return (
    <div className="main-dialog">
      <h1>{title}</h1>
      <div className="dialog-wrapper">
        {header}
        <div className="dialog-content">
          {content}
        </div>
      </div>
    </div>
  );
}
