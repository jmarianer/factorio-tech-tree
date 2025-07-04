import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { Item } from './FactorioData';

export function ItemIcon({ item }: { item: Item }) {
  const { regime } = useParams();
  return <Link to={`/${regime}/${item.type}/${item.name}`} key={item.name}>
    <img className='icon' src={`/generated/${regime}/icons/${item.type}/${item.name}.png`} alt={item.name} />
  </Link>;
} 