// Navbar.jsx - Professional Navigation Bar with Integrated Search

import React from 'react';
import { NavLink } from 'react-router-dom';

function Navbar({ isDarkMode, toggleTheme }) {
  return (
    <nav className="navbar-professional">
      <div className="navbar-content">
        {/* Left: Brand */}
        <div className="navbar-brand">
          <div className="brand-icon">🌍</div>
          <div className="brand-text">
            <h1 className="brand-name">AirQuality</h1>
            <p className="brand-subtitle">Monitor</p>
          </div>
        </div>
        
        {/* Center: Navigation Tabs */}
        <div className="navbar-center">
          <div className="nav-tabs-center">
            <NavLink
              to="/"
              end
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-link-icon">📊</span>
              <span className="nav-link-text">Today</span>
            </NavLink>
            <NavLink
              to="/history"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-link-icon">📅</span>
              <span className="nav-link-text">History</span>
            </NavLink>
          </div>
        </div>
        
        {/* Right: Search & Theme Toggle */}
        <div className="navbar-right">
          <div className="search-bar-integrated">
            <span className="search-icon-integrated">�</span>
            <input 
              type="text" 
              placeholder="Search location..." 
              className="search-input-integrated"
            />
          </div>
          
          <button
            onClick={toggleTheme}
            className="theme-toggle-btn"
            aria-label="Toggle theme"
            title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            <span className="theme-icon">
              {isDarkMode ? '☀️' : '🌙'}
            </span>
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
