import { useParams } from 'react-router-dom';
import { Dialog } from './Dialog';
import { useData } from './DataContext';

export default function Item() {
  const { regime, type, name } = useParams();
  const data = useData();
  const item = data.items[name!];

  return Dialog(`Item: ${item.localized_title('en')}`,
    <img src={`/generated/${regime}/icons/${type}/${name}.png`} alt={name} />,
    <div>
      <h1>{item.localized_title('en')}</h1>
      <p>{item.description('en')}</p>
    </div>
  );
}
