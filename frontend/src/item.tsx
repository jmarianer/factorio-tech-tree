import { Link, useParams } from 'react-router-dom';
import { Dialog } from './Dialog';
import { useData } from './DataContext';
import { ItemWithCount } from './FactorioTypes';
import { ItemIcon, RenderRecipe } from './Elements';
import { BBCode } from './BBCode';

export function RenderItemWithCount({ itemWithCount }: { itemWithCount: ItemWithCount }) {
  return (
    <div style={{ position: 'relative' }}>
      <span className="quantity">{itemWithCount.quantity}</span>
      <ItemIcon item={itemWithCount.item} />
    </div>
  );
}

export default function Item() {
  const { regime, name } = useParams();
  const data = useData();
  const item = data.items[name!];

  return Dialog(`Item: ${item.localized_title('en')}`,
    <>
      <img src={`/generated/${regime}/icons/${item.type}/${name}.png`} alt={name} />
      <div className="description">
        <BBCode code={item.description('en')} />
      </div>
    </>,
    <>
      <h2>Produced in</h2>
      <div className="recipe-list">
        {item.produced_in.map(recipe => (
          <RenderRecipe key={recipe.name} recipe={recipe} />
        ))}
      </div>
      <h2>Used in</h2>
      <div className="recipe-list">
        {item.used_in.map(recipe => (
          <RenderRecipe key={recipe.name} recipe={recipe} />
        ))}
      </div>
      {item.placement_result && (
        <>
          <h2>Entity: {item.placement_result.localized_title('en')}</h2>
          <Link to={`/${regime}/entity/${item.placement_result.name}`}>More info</Link>
        </>
      )}
    </>
  );
}
