import { useParams } from 'react-router-dom';
import { Dialog } from './Dialog';

export default function Item() {
  const { regime, type, name } = useParams();
  return Dialog(`Item: ${name}`,
    <img src={`/generated/${regime}/icons/${type}/${name}.png`} alt={name} />,
    <div>
      <h1>{name}</h1>
      <p>{type}</p>
    </div>
  );
}
