// App.jsx - Main Application Component

import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import TodayView from "./components/TodayView.jsx";
import HistoryView from "./components/HistoryView.jsx";
import "./App.css"; // Main application styles

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Routes>
          <Route path="/" element={<TodayView />} />
          <Route path="/history" element={<HistoryView />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
