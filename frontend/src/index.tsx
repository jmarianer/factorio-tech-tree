import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { DataProvider } from './DataContext';
import Home from './home';
import Item from './item';
import Entity from './entity';
import Recipe from './recipe';
import './factorio.css';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

const regimes = [
  ["base", "Base"],
  ["spacex", "Space Exploration"],
  ["ind", "Industrial Revolution"],
  ["k2spacex", "Space Exploration + Krastorio 2"]
];

function ListRegimes() {
  return <div>
    <h1>Regimes</h1>
    <ul>
      {regimes.map(([regime, name]) => (
        <li key={regime}>
          <Link to={`/${regime}`}>{name}</Link>
        </li>
      ))}
    </ul>
  </div>;
}

function RegimeLayout() {
  return <DataProvider>
    <Routes>
      <Route path="/" element={<Home />} />
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