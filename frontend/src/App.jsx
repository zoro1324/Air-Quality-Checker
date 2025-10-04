// App.js (Conceptual Structure)

import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Header from "./components/Header.jsx";
import TodayView from "./components/TodayView.jsx";
import HistoryView from "./components/HistoryView.jsx";
import "./App.css"; // Main application styles

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Header />
        <Routes>
          <Route path="/" element={<TodayView />} />
          <Route path="/history" element={<HistoryView />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
