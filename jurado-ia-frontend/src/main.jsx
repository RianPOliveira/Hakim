import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App.jsx'; // Nosso componente de Layout
import HomePage from './pages/HomePage.jsx'; // Nossa página de Início
import AboutPage from './pages/AboutPage.jsx'; // Nossa página Sobre
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          {/* A HomePage será renderizada no <Outlet /> quando a URL for "/" */}
          <Route index element={<HomePage />} />
          {/* A AboutPage será renderizada no <Outlet /> quando a URL for "/sobre" */}
          <Route path="sobre" element={<AboutPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)