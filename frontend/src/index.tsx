import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { DataProvider } from './DataContext';
import AllItems from './allitems';
import Item from './item';
import Entity from './entity';
import Recipe from './recipe';
import './factorio.css';
import { TechTree } from './techtree';
import { Dialog } from './Dialog';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

const regimes = [
  ["base", "Base"],
  ["spacex", "Space Exploration"],
  ["ind", "Industrial Revolution"],
  ["k2spacex", "Space Exploration + Krastorio 2"],
  ["angelbobs", "Angel's and Bob's Mods"]
];

function ListRegimes() {
  return Dialog('Select a regime',
    <></>,
    <div>
      {regimes.map(([regime, name]) => (
        <Link className="regime" key={regime} to={`/${regime}`}>{name}</Link>
      ))}
    </div>
  );
}

function RegimeLayout() {
  return <DataProvider>
    <Routes>
      <Route path="/" element={<AllItems />} />
      <Route path="/tech" element={<TechTree />} />
      <Route path="/recipe/:name" element={<Recipe />} />
      <Route path="/item/:name" element={<Item />} />
      <Route path="/entity/:name" element={<Entity />} />
    </Routes>
  </DataProvider>;
}

root.render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<ListRegimes />} />
        <Route path="/:regime/*" element={<RegimeLayout />} />
      </Routes>
    </Router>
  </React.StrictMode>
);