import { useParams } from "react-router-dom";
import { useData } from "./DataContext";
import { Dialog } from "./Dialog";
import { BBCode } from "./BBCode";
import { ItemWithCount } from './FactorioTypes';
import { ItemIcon } from "./Elements";
import { FactorioData } from './FactorioData';

function RenderItemWithCount({ itemWithCount }: { itemWithCount: ItemWithCount }) {
  return (
    <tr>
      <td style={{ textAlign: 'right' }}>{itemWithCount.quantity}</td>
      <td><ItemIcon item={itemWithCount.item} /></td>
      <td>{itemWithCount.localized_title('en')}</td>
    </tr>
  );
}

export default function Recipe() {
  const { regime, name } = useParams();
  const data = useData<FactorioData>();
  const recipe = data.recipes[name!];
  return Dialog(`Recipe: ${recipe.name}`,
    <>
      <img src={`/generated/${regime}/icons/${recipe.type}/${recipe.name}.png`} alt={recipe.name} />
      <div className="description">
        <BBCode code={recipe.description('en')} />
      </div>
    </>,
    <div style={{ display: "flex", justifyContent: "space-between" }}>
      <div>
        <h2>Inputs</h2>
        <table>
          {recipe.ingredients.map((ingredient) => (
            <RenderItemWithCount key={ingredient.name} itemWithCount={ingredient} />
          ))}
        </table>
      </div>
      <div>
        <h2>Outputs:</h2>
        <table>
          {recipe.products.map((product) => (
            <RenderItemWithCount key={product.name} itemWithCount={product} />
          ))}
        </table>
      </div>
      <div>
        <h2>Crafted in:</h2>
        {recipe.crafted_in.map(([entity, time]) => (
          <a key={entity.name} className="item" href={`item_${entity.name}.html`}>
            {/* TODO entity icon here! <ItemIcon entity={entity} /> */}
            {entity.localized_title('en')} ({time.toFixed(2)}s)
          </a>
        ))}
      </div>
    </div>
  );
}