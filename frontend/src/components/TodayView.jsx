// TodayView.jsx - renders the Today dashboard including a dummy doughnut chart

import React from "react";
import { Doughnut } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend);

function PollutantChart() {
  const data = {
    labels: ["PM2.5", "PM10", "NO2", "O3"],
    datasets: [
      {
        data: [40, 30, 20, 10],
        backgroundColor: ["#60bf6f", "#5aa3ff", "#ffd966", "#e54c3c"],
        borderWidth: 0,
      },
    ],
  };

  const options = {
    cutout: "65%",
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: true,
      },
    },
    maintainAspectRatio: false,
  };

  return (
    <div className="pollutant-card">
      <div className="pollutant-info">
        <div className="pie-chart-left">
          <div className="pie-chart-container">
            <Doughnut data={data} options={options} />
            <div className="donut-center">100%</div>
          </div>
        </div>

        <div className="pollutant-text">
          <h2 className="dominant-pollutant-title">Dominant Pollutant:</h2>
            <h1 className="pollutant-name">PM2.5</h1>
          <button className="health-advice-button">Health advice</button>
        </div>
      </div>
    </div>
  );
}

function WeatherReport() {
  return (
    <div className="weather-card">
      <h3 className="weather-title">Weather report</h3>
      <div className="temperature">
        <span></span>
        <span>30</span>
      </div>
      <p>Humidity:</p>
      <p>Sunny:</p>
      <p>Windy:</p>
    </div>
  );
}

function TodayView() {
  return (
    <div className="today-view">
      <PollutantChart />
      <WeatherReport />
      {/* Four empty white boxes at the bottom */}
      <h2>Suggested Crops</h2>
      <div className="bottom-sections">
        <div className="bottom-box">
          <h3 className="bottom-box-text">Rice</h3>
        </div>
        <div className="bottom-box">
          <h3 className="bottom-box-text">Wheat</h3>
        </div>
        <div className="bottom-box">
          <h3 className="bottom-box-text">Maize</h3>
        </div>
        <div className="bottom-box">
          <h3 className="bottom-box-text">Tomato</h3>
        </div>
      </div>
    </div>
  );
}

export default TodayView;
