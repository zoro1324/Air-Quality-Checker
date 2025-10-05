// Header.js (Conceptual Structure)

import React from "react";
import { NavLink } from "react-router-dom";
import { MdLocationOn, MdSearch } from "react-icons/md";

function Header() {
  return (
    <header className="header">
      <div className="logo"></div>
      <div className="search-area">
        <span className="location-pin">
          <MdLocationOn size={20} />
        </span>
        <input type="text" placeholder="Search location..." />
        <button className="search-button">
          <MdSearch size={20} />
        </button>
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
