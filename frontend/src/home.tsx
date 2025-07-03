import React, { useContext, useState } from 'react';
import { DataContext } from './DataContext';
import _ from 'lodash';

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
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);

  if (loading) {
    return <div>Loading...</div>;
  }
  if (!data) {
    return <div>No data: {error?.message}</div>;
  }

  const grouped_items = _(data.items)
    .filter(item => !item.hidden && !item.flags.includes('hidden'))
    .groupBy('subgroup.name')
    .orderBy((items) => items[0].subgroup.order)
    .groupBy((items) => items[0].subgroup.group.name);

  const groups = grouped_items
    .keys()
    .map((group_name) => data.groups[group_name])
    .orderBy((group) => group.order)
    .value();

  if (!selectedGroup) {
    setSelectedGroup(groups[0].name);
  }

  return Dialog('All items',
    <>
      {groups.map((group) => (
        <div className="group-container" key={group.name}>
          <h2 className="group" onClick={() => setSelectedGroup(group.name)}>
            <img src={`generated/base/icons/item-group/${group.name}.png`} alt={group.name} />
            {group.name}
          </h2>
        </div>
      ))}
    </>,
    <>
      {selectedGroup && grouped_items.get(selectedGroup).map((subgroup) => <>
          {_(subgroup)
            .orderBy((item) => item.order)
            .value()
            .map((item) => <img className='icon' src={`generated/base/icons/${item.type}/${item.name}.png`} alt={item.name} />)}
          <br />
      </>)}
    </>);
}
