import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { Item, ItemWithCount, Recipe } from './FactorioTypes';
import { RenderItemWithCount } from './item';

export function ItemIcon({ item }: { item: Item }) {
  const { regime } = useParams();
  return <Link to={`/${regime}/item/${item.name}`} key={item.name}>
    <img className='icon' src={`/generated/${regime}/icons/${item.type}/${item.name}.png`} alt={item.name} />
  </Link>;
}

export function RenderRecipe({ recipe }: { recipe: Recipe; }) {
  const { regime } = useParams();
  return (
    <div className="recipe-container">
      <div className="recipe">
        {recipe.ingredients.map((ingredient: ItemWithCount) => (
          <RenderItemWithCount key={ingredient.name} itemWithCount={ingredient} />
        ))}
        <img src="/chevron.svg" className="chevron" alt="into" />
        {recipe.products.map((product: ItemWithCount) => (
          <RenderItemWithCount key={product.name} itemWithCount={product} />
        ))}
      </div>
      <Link to={`/${regime}/recipe/${recipe.name}`} className="more-info">
        <img src="/double-chevron.svg" className="double-chevron" alt="More info" />
      </Link>
    </div>
  );
}
 