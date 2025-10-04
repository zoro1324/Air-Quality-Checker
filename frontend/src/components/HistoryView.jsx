// HistoryView.jsx - AQI Prediction and Analysis

import React, { useState, useEffect, createContext } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { API_ENDPOINTS, fetchAPI } from '../config/api.js';
import Navbar from './Navbar.jsx';
import useGeolocation from '../hooks/useGeolocation.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Theme Context
const ThemeContext = createContext();

function HistoryView() {
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [historyData, setHistoryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const userLocation = useGeolocation();

  // Initialize theme from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = savedTheme === 'dark' || (!savedTheme && true);
    setIsDarkMode(prefersDark);
    document.documentElement.classList.toggle('dark', prefersDark);
  }, []);

  const toggleTheme = () => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
    document.documentElement.classList.toggle('dark', newTheme);
  };

  // Set default dates (last 7 days)
  useEffect(() => {
    const today = new Date();
    const lastWeek = new Date();
    lastWeek.setDate(lastWeek.getDate() - 7);
    
    setStartDate(lastWeek.toISOString().split('T')[0]);
    setEndDate(today.toISOString().split('T')[0]);
  }, []);

  const fetchPredictionData = async () => {
    if (!startDate || !endDate) {
      setError('Please select both start and end dates');
      return;
    }

    if (new Date(startDate) > new Date(endDate)) {
      setError('Start date must be before end date');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const startTimestamp = new Date(startDate + 'T00:00:00Z').getTime() / 1000;
      const endTimestamp = new Date(endDate + 'T23:59:59Z').getTime() / 1000;

      const params = new URLSearchParams({
        start: Math.floor(startTimestamp).toString(),
        end: Math.floor(endTimestamp).toString(),
      });

      if (userLocation.latitude && userLocation.longitude) {
        params.append('lat', userLocation.latitude.toString());
        params.append('lon', userLocation.longitude.toString());
      }

      const data = await fetchAPI(`${API_ENDPOINTS.PREDICT_AQI}?${params.toString()}`);
      console.log('API Response:', data);
      setHistoryData(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch prediction data');
      setHistoryData(null);
    } finally {
      setLoading(false);
    }
  };

  const themeValue = { isDarkMode, toggleTheme };

  return (
    <ThemeContext.Provider value={themeValue}>
      <div className="history-view-container">
        <Navbar isDarkMode={isDarkMode} toggleTheme={toggleTheme} />
        
        <div className="content-wrapper">
          <div className="history-header">
            <h1 className="history-title">AQI Prediction & Analysis</h1>
            <p className="history-subtitle">Predict and analyze air quality trends for any time period</p>
          </div>

          <DateRangeSelector
            startDate={startDate}
            endDate={endDate}
            setStartDate={setStartDate}
            setEndDate={setEndDate}
            onFetch={fetchPredictionData}
            loading={loading}
            userLocation={userLocation}
          />

          {error && (
            <div className="history-error">
              <span className="error-icon">⚠️</span>
              <p>{error}</p>
            </div>
          )}

          {loading && (
            <div className="history-loading">
              <div className="spinner-large"></div>
              <p>Predicting AQI data...</p>
            </div>
          )}

          {historyData && !loading && (
            <>
              <HistoryChart data={historyData} />
              <HistoryStats data={historyData} />
            </>
          )}
        </div>
      </div>
    </ThemeContext.Provider>
  );
}

function DateRangeSelector({ startDate, endDate, setStartDate, setEndDate, onFetch, loading, userLocation }) {
  return (
    <div className="date-range-card">
      <div className="date-range-header">
        <h3 className="date-range-title">Select Time Period for Prediction</h3>
        {userLocation.city && (
          <div className="location-display">
            <span className="location-pin">📍</span>
            <span className="location-name">{userLocation.city}</span>
          </div>
        )}
      </div>
      
      <div className="date-inputs-grid">
        <div className="date-input-group">
          <label htmlFor="start-date">Start Date</label>
          <input
            id="start-date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="date-input-modern"
            max={endDate || new Date().toISOString().split('T')[0]}
          />
        </div>
        
        <div className="date-input-group">
          <label htmlFor="end-date">End Date</label>
          <input
            id="end-date"
            type="date"
            value={endDate}
            onChange={(e) => {
              console.log('End date changed:', e.target.value);
              setEndDate(e.target.value);
            }}
            className="date-input-modern"
            min={startDate}
          />
        </div>
      </div>

      <button
        onClick={onFetch}
        disabled={loading || !startDate || !endDate}
        className="fetch-data-button"
      >
        <span className="button-icon">�</span>
        <span className="button-text">{loading ? 'Predicting...' : 'Predict AQI'}</span>
      </button>
    </div>
  );
}

function HistoryChart({ data }) {
  // API returns 'results' array, not 'history'
  const results = data?.results || [];
  
  if (results.length === 0) {
    return (
      <div className="chart-empty">
        <p>No prediction data available for the selected period</p>
      </div>
    );
  }

  // Dynamic label thinning based on data size
  const getDataInterval = (dataLength) => {
    if (dataLength <= 24) return 1;      // Show all (hourly for 1 day)
    if (dataLength <= 72) return 3;      // Every 3 hours (2-3 days)
    if (dataLength <= 168) return 6;     // Every 6 hours (4-7 days)
    if (dataLength <= 336) return 12;    // Every 12 hours (8-14 days)
    return 24;                            // Daily (15+ days)
  };

  const interval = getDataInterval(results.length);

  // Create datasets for multiple pollutants
  const chartData = {
    labels: results.map((item, index) => {
      const date = new Date(item.timestamp_utc * 1000);
      // Show label only at intervals
      if (index % interval === 0 || index === results.length - 1) {
        if (results.length <= 72) {
          // Show hours for short periods
          return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit' });
        } else {
          // Show only date for longer periods
          return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        }
      }
      return ''; // Empty label for non-interval points
    }),
    datasets: [
      {
        label: 'Predicted AQI',
        data: results.map(item => item.predicted_aqi || item.openweather_aqi || 0),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 6,
        borderWidth: 2,
      },
      {
        label: 'PM2.5 (μg/m³)',
        data: results.map(item => item.components?.pm2_5 || 0),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 5,
        borderWidth: 2,
        yAxisID: 'y1',
      },
      {
        label: 'PM10 (μg/m³)',
        data: results.map(item => item.components?.pm10 || 0),
        borderColor: 'rgb(249, 115, 22)',
        backgroundColor: 'rgba(249, 115, 22, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 5,
        borderWidth: 2,
        yAxisID: 'y1',
      },
      {
        label: 'NO₂ (μg/m³)',
        data: results.map(item => item.components?.no2 || 0),
        borderColor: 'rgb(139, 92, 246)',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 5,
        borderWidth: 2,
        yAxisID: 'y1',
      },
      {
        label: 'O₃ (μg/m³)',
        data: results.map(item => item.components?.o3 || 0),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 5,
        borderWidth: 2,
        yAxisID: 'y1',
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: getComputedStyle(document.documentElement).getPropertyValue('--text-primary'),
          font: { size: 14, weight: '600' },
        },
      },
      tooltip: {
        backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--bg-tertiary'),
        titleColor: getComputedStyle(document.documentElement).getPropertyValue('--text-primary'),
        bodyColor: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary'),
        borderColor: getComputedStyle(document.documentElement).getPropertyValue('--border-color'),
        borderWidth: 1,
        padding: 12,
        displayColors: true,
      },
    },
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        beginAtZero: true,
        title: {
          display: true,
          text: 'AQI Index',
          color: getComputedStyle(document.documentElement).getPropertyValue('--text-primary'),
          font: { size: 12, weight: '600' },
        },
        grid: {
          color: getComputedStyle(document.documentElement).getPropertyValue('--border-color'),
        },
        ticks: {
          color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary'),
        },
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        beginAtZero: true,
        title: {
          display: true,
          text: 'Pollutant Concentration (μg/m³)',
          color: getComputedStyle(document.documentElement).getPropertyValue('--text-primary'),
          font: { size: 12, weight: '600' },
        },
        grid: {
          drawOnChartArea: false,
        },
        ticks: {
          color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary'),
        },
      },
      x: {
        grid: {
          color: getComputedStyle(document.documentElement).getPropertyValue('--border-color'),
        },
        ticks: {
          color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary'),
          maxRotation: 45,
          minRotation: 45,
          autoSkip: false,
          maxTicksLimit: 20,
          callback: function(value) {
            // Only show non-empty labels
            const label = this.getLabelForValue(value);
            return label || undefined;
          },
        },
      },
    },
  };

  return (
    <div className="history-chart-card">
      <h3 className="chart-title">Predicted AQI Trend</h3>
      <div className="chart-container-history">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}

function HistoryStats({ data }) {
  const results = data?.results || [];
  if (results.length === 0) return null;

  const aqiValues = results.map(item => item.predicted_aqi || item.openweather_aqi || 0);
  const avgAqi = (aqiValues.reduce((a, b) => a + b, 0) / aqiValues.length).toFixed(1);
  const maxAqi = Math.max(...aqiValues);
  const minAqi = Math.min(...aqiValues);
  const dataPoints = results.length;

  const stats = [
    { label: 'Average AQI', value: avgAqi, icon: '📊', color: '#3b82f6' },
    { label: 'Maximum AQI', value: maxAqi, icon: '⬆️', color: '#ef4444' },
    { label: 'Minimum AQI', value: minAqi, icon: '⬇️', color: '#10b981' },
    { label: 'Data Points', value: dataPoints, icon: '📈', color: '#8b5cf6' },
  ];

  return (
    <div className="history-stats-grid">
      {stats.map((stat, index) => (
        <div key={index} className="stat-card" style={{ '--stat-color': stat.color }}>
          <div className="stat-icon">{stat.icon}</div>
          <div className="stat-content">
            <p className="stat-label">{stat.label}</p>
            <p className="stat-value">{stat.value}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default HistoryView;