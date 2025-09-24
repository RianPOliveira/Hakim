import React, { useState, useEffect } from 'react';
import { Link, Outlet } from 'react-router-dom';
import './App.css';

// --- ÍCONE DO ROBÔ (SVG Embutido) ---
const RobotIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" viewBox="0 0 16 16">
    <path d="M8 1a2.5 2.5 0 0 1 2.5 2.5V4h-5v-.5A2.5 2.5 0 0 1 8 1zM3.5 5a1 1 0 0 0-1 1v1.5a.5.5 0 0 1-1 0V6a2 2 0 0 1 2-2h1a.5.5 0 0 1 0 1h-1zM11.5 4h1a2 2 0 0 1 2 2v1.5a.5.5 0 0 1-1 0V6a1 1 0 0 0-1-1h-1a.5.5 0 0 1 0-1z"/>
    <path d="M9.5 7a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0v-1a.5.5 0 0 1 .5-.5zm-3 0a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0v-1a.5.5 0 0 1 .5-.5z"/>
    <path d="M2 9.5a3.5 3.5 0 0 0 3.5 3.5h7A3.5 3.5 0 0 0 16 9.5v-2a3.5 3.5 0 0 0-3.5-3.5h-7A3.5 3.5 0 0 0 2 7.5v2zm3.5-2.5a2.5 2.5 0 0 1 2.5-2.5h7a2.5 2.5 0 0 1 2.5 2.5v2a2.5 2.5 0 0 1-2.5-2.5h-7a2.5 2.5 0 0 1-2.5-2.5v-2z"/>
  </svg>
);

// --- Componente de Layout Principal ---
function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');

  useEffect(() => {
    document.body.className = '';
    document.body.classList.add(`${theme}-theme`);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  return (
    <div className="App-wrapper">
      
      {/* ÍCONES DECORATIVOS DE FUNDO */}
      <div className="background-icons">
        <i className="fas fa-gavel"></i>
        <i className="fas fa-file-alt"></i>
        <i className="fas fa-chart-bar"></i>
        <i className="fas fa-balance-scale"></i>
        <i className="fas fa-microchip"></i>
        <i className="fas fa-search"></i>
      </div>

      <nav className="top-nav">
        <div className="container">
          <Link to="/" className="logo-link">
            <span className="logo">
              <RobotIcon /> 
              Jurado IA
            </span>
          </Link>
          <div className="nav-links">
            <Link to="/">Início</Link>
            <Link to="/sobre">Sobre</Link>
            <div className="theme-switch-wrapper">
              <label className="theme-switch" htmlFor="theme-checkbox">
                <input
                  type="checkbox"
                  id="theme-checkbox"
                  checked={theme === 'dark'}
                  onChange={toggleTheme}
                />
                <div className="slider">
                  <div className="icon-wrapper">
                    <i className="fas fa-sun"></i>
                    <i className="fas fa-moon"></i>
                  </div>
                </div>
              </label>
            </div>
          </div>
        </div>
      </nav>
      <main>
        {/* As páginas (Início e Sobre) serão renderizadas aqui pelo Outlet */}
        <Outlet /> 
      </main>
    </div>
  );
}

export default App;