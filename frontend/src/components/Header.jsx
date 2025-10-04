// Header.js (Conceptual Structure)

import React from "react";
import { NavLink } from "react-router-dom";

function Header() {
  return (
    <header className="header">
      <div className="logo"></div>
      <div className="search-area">
        <span className="location-pin">📍</span>
        <input type="text" placeholder="Search location..." />
        <button className="search-button">🔍</button>
      </div>
      <div className="tabs">
        <NavLink
          to="/"
          end
          className={({ isActive }) => `tab ${isActive ? "active" : ""}`}
        >
          Today
        </NavLink>
        <NavLink
          to="/history"
          className={({ isActive }) => `tab ${isActive ? "active" : ""}`}
        >
          History
        </NavLink>
      </div>
    </header>
  );
}

export default Header;
