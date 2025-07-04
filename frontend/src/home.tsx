import React, { useState } from 'react';
import { useData } from './DataContext';
import _ from 'lodash';
import { useParams } from 'react-router-dom';
import { Dialog } from './Dialog';
import { ItemIcon } from './Elements';

export default function Home() {
  const { regime } = useParams();
  const data = useData();
  const [selectedGroup, setSelectedGroup] = useState<string | null>(() => {
    return window.location.hash.slice(1) || null;
  });
  React.useEffect(() => {
    if (selectedGroup) {
      window.location.hash = selectedGroup;
    }
  }, [selectedGroup]);

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
            <img src={`/generated/${regime}/icons/item-group/${group.name}.png`} alt={group.name} />
            {group.localized_title('en')}
          </h2>
        </div>
      ))}
    </>,
    <>
      {selectedGroup && grouped_items.get(selectedGroup).map((subgroup) => <div key={subgroup[0].name}>
          {_(subgroup)
            .orderBy((item) => item.order)
            .value()
            .map((item) => <ItemIcon key={item.name} item={item} />)}
          <br />
      </div>)}
    </>);
}
