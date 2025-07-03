import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { DataProvider } from './DataContext';
import Home from './home';
import './factorio.css';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <DataProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/foo" element={<Link to="/">Foo</Link>} />
        </Routes>
      </Router>
    </DataProvider>
  </React.StrictMode>
);