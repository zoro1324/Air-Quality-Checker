// Navbar.jsx - Professional Navigation Bar with Integrated Search

import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  MdPublic, 
  MdDashboard, 
  MdCalendarMonth, 
  MdSearch, 
  MdLightMode, 
  MdDarkMode 
} from 'react-icons/md';

function Navbar({ isDarkMode, toggleTheme }) {
  return (
    <nav className="navbar-professional">
      <div className="navbar-content">
        {/* Left: Brand */}
        <div className="navbar-brand">
          <div className="brand-icon"><img src="/public/logo.png" style={{ width: '32px', height: '32px' }} alt="Aero Guardian Logo" /></div>
          <div className="brand-text">
            <h1 className="brand-name">Aero Gaurdian</h1>
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
              <span className="nav-link-icon"><MdDashboard size={20} /></span>
              <span className="nav-link-text">Today</span>
            </NavLink>
            <NavLink
              to="/history"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-link-icon"><MdCalendarMonth size={20} /></span>
              <span className="nav-link-text">Analysis</span>
            </NavLink>
          </div>
        </div>
        
        {/* Right: Search & Theme Toggle */}
        <div className="navbar-right">
          <div className="search-bar-integrated">
            <span className="search-icon-integrated"><MdSearch /></span>
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
              {isDarkMode ? <MdLightMode size={24} /> : <MdDarkMode size={24} />}
            </span>
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
