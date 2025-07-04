import { Link, useParams } from 'react-router-dom';
import { Dialog } from './Dialog';
import { useData } from './DataContext';
import { ItemWithCount, Recipe } from './FactorioTypes';
import { ItemIcon } from './Elements';
import { BBCode } from './BBCode';

function RenderItemWithCount({ itemWithCount }: { itemWithCount: ItemWithCount }) {
  return (
    <div style={{ position: 'relative' }}>
      <span className="quantity">{itemWithCount.quantity}</span>
      <ItemIcon item={itemWithCount.item} />
    </div>
  );
}

function RenderRecipe({ recipe }: { recipe: Recipe }) {
  const { regime } = useParams();
  return (
    <div className="recipe-container">
      <div className="recipe">
        {recipe.ingredients.map((ingredient: ItemWithCount) => (
          <RenderItemWithCount key={ingredient.name} itemWithCount={ingredient} />
        ))}
        <img src="/chevron.svg" className="chevron" />
        {recipe.products.map((product: ItemWithCount) => (
          <RenderItemWithCount key={product.name} itemWithCount={product} />
        ))}
      </div>
      <Link to={`/${regime}/recipe/${recipe.name}`} className="more-info">
        <img src="/double-chevron.svg" className="double-chevron" />
      </Link>
    </div>
  );
}

export default function Item() {
  const { regime, type, name } = useParams();
  const data = useData();
  const item = data.items[name!];

  return Dialog(`Item: ${item.localized_title('en')}`,
    <>
      <img src={`/generated/${regime}/icons/${type}/${name}.png`} alt={name} />
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
    </>
  );
}
