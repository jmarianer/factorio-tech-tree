import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { DataProvider } from './DataContext';
import Home from './home';
import Item from './item';
import Recipe from './recipe';
import './factorio.css';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

function RegimeLayout() {
  return <DataProvider>
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/recipe/:name" element={<Recipe />} />
      <Route path="/:type/:name" element={<Item />} />
    </Routes>
  </DataProvider>;
}

root.render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/:regime/*" element={<RegimeLayout />} />
      </Routes>
    </Router>
  </React.StrictMode>
);