// TodayView.jsx - Professional Air Quality Dashboard

import React, { useState, useEffect, createContext } from "react";
import { Doughnut } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { API_ENDPOINTS, fetchAPI } from "../config/api.js";
import useGeolocation from "../hooks/useGeolocation.js";
import Navbar from "./Navbar.jsx";
import TextToSpeech from "./TextToSpeech.jsx";

ChartJS.register(ArcElement, Tooltip, Legend);

// Theme Context
const ThemeContext = createContext();

// Helper function to get AQI level and color
const getAQIInfo = (aqi) => {
  if (aqi <= 50) return { 
    level: "Good", 
    color: "#10b981", 
    textColor: "#fff",
    gradient: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
    description: "Air quality is satisfactory, and air pollution poses little or no risk."
  };
  if (aqi <= 100) return { 
    level: "Moderate", 
    color: "#f59e0b", 
    textColor: "#000",
    gradient: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
    description: "Air quality is acceptable. However, there may be a risk for some people."
  };
  if (aqi <= 150) return { 
    level: "Unhealthy for Sensitive", 
    color: "#f97316", 
    textColor: "#fff",
    gradient: "linear-gradient(135deg, #f97316 0%, #ea580c 100%)",
    description: "Members of sensitive groups may experience health effects."
  };
  if (aqi <= 200) return { 
    level: "Unhealthy", 
    color: "#ef4444", 
    textColor: "#fff",
    gradient: "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
    description: "Some members of the general public may experience health effects."
  };
  if (aqi <= 300) return { 
    level: "Very Unhealthy", 
    color: "#a855f7", 
    textColor: "#fff",
    gradient: "linear-gradient(135deg, #a855f7 0%, #9333ea 100%)",
    description: "Health alert: The risk of health effects is increased for everyone."
  };
  return { 
    level: "Hazardous", 
    color: "#7c2d12", 
    textColor: "#fff",
    gradient: "linear-gradient(135deg, #7c2d12 0%, #431407 100%)",
    description: "Health warning of emergency conditions. Everyone is more likely to be affected."
  };
};

function AQICard({ aqiData, loading, error }) {
  if (loading) {
    return (
      <div className="aqi-main-card loading-state">
        <div className="loading-content">
          <div className="spinner"></div>
          <p>Loading Air Quality Data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="aqi-main-card error-state">
        <div className="error-content">
          <div className="error-icon">⚠️</div>
          <h3>Unable to Load AQI Data</h3>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const pollutants = aqiData?.results || [];
  const aqi = aqiData?.aqi || 0;
  const aqiInfo = getAQIInfo(aqi);

  // Prepare chart data with percentages
  const chartPollutants = pollutants.filter(p => p.value !== null && p.value !== undefined).slice(0, 6);
  const labels = chartPollutants.map(p => p.pollutant);
  const values = chartPollutants.map(p => p.value);
  const totalValue = values.reduce((sum, val) => sum + val, 0);
  const percentages = values.map(val => ((val / totalValue) * 100));
  const colors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#a855f7", "#ec4899"];

  const data = {
    labels: labels,
    datasets: [
      {
        data: percentages,
        backgroundColor: colors.slice(0, percentages.length),
        borderWidth: 2,
        borderColor: '#ffffff',
        hoverOffset: 8,
      },
    ],
  };

  const options = {
    cutout: "70%",
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        padding: 12,
        titleFont: { size: 14, weight: 'bold' },
        bodyFont: { size: 13 },
        callbacks: {
          label: function(context) {
            const value = values[context.dataIndex];
            const percentage = context.parsed;
            return [
              `Value: ${value.toFixed(2)} μg/m³`,
              `Contribution: ${percentage.toFixed(1)}%`
            ];
          }
        }
      },
    },
    maintainAspectRatio: false,
  };

  return (
    <div className="aqi-main-card">
      <div className="aqi-header">
        <div className="aqi-badge" style={{ 
          background: aqiInfo.gradient,
          color: aqiInfo.textColor 
        }}>
          <span className="aqi-label">AQI</span>
          <span className="aqi-value">{aqi}</span>
        </div>
        <h2 className="aqi-level" style={{ color: aqiInfo.color }}>
          {aqiInfo.level}
        </h2>
      </div>

      <div className="aqi-content">
        <div className="aqi-chart-section">
          <div className="chart-wrapper">
            {values.length > 0 ? (
              <>
                <Doughnut data={data} options={options} />
                <div className="chart-center-label">
                  <div className="center-pollutant">AQI</div>
                  <div className="center-value" style={{ color: aqiInfo.color }}>{aqi}</div>
                  <div className="center-unit">{aqiInfo.level}</div>
                </div>
              </>
            ) : (
              <div className="no-data-message">No data available</div>
            )}
          </div>
          <div className="chart-legend">
            {chartPollutants.slice(0, 6).map((p, idx) => (
              <div key={idx} className="legend-item">
                <span className="legend-dot" style={{ backgroundColor: colors[idx] }}></span>
                <span className="legend-label">{p.pollutant}</span>
                <span className="legend-value">{percentages[idx]?.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>

        <div className="aqi-info-section">
          <h3 className="info-title">Air Quality Impact</h3>
          <p className="info-description">{aqiInfo.description}</p>
          
          <div className="pollutant-grid">
            {pollutants.slice(0, 4).map((p, idx) => (
              <div key={idx} className="pollutant-stat">
                <div className="stat-label">{p.pollutant}</div>
                <div className="stat-value">{p.value?.toFixed(2) || 'N/A'}</div>
                <div className="stat-unit">{p.units}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function WeatherCard({ weatherData, loading, error }) {
  if (loading) {
    return (
      <div className="weather-main-card loading-state">
        <div className="loading-content">
          <div className="spinner"></div>
          <p>Loading Weather...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="weather-main-card error-state">
        <div className="error-content">
          <div className="error-icon">⚠️</div>
          <h3>Unable to Load Weather</h3>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const result = weatherData?.result || {};
  const location = result.location || {};
  const conditions = result.conditions || {};
  const temperature = result.temperature || {};
  const atmosphere = result.atmosphere || {};
  const wind = result.wind || {};

  const tempValue = temperature.value || 0;
  const tempUnit = temperature.units === 'metric' ? '°C' : temperature.units === 'imperial' ? '°F' : 'K';
  const weatherIcon = conditions.icon ? `https://openweathermap.org/img/wn/${conditions.icon}@4x.png` : null;

  return (
    <div className="weather-main-card">
      <div className="weather-header">
        <div className="weather-location">
          <div className="location-icon">📍</div>
          <div className="location-details">
            <h3>{location.name || 'Unknown'}</h3>
            <p>{location.country || ''}</p>
          </div>
        </div>
      </div>

      <div className="weather-current">
        {weatherIcon && (
          <div className="weather-icon-wrapper">
            <img src={weatherIcon} alt={conditions.description} className="weather-icon-large" />
          </div>
        )}
        <div className="weather-temp-main">
          <div className="temp-display">{tempValue.toFixed(1)}<span className="temp-unit">{tempUnit}</span></div>
          <div className="weather-desc">{conditions.description || 'Clear'}</div>
          <div className="feels-like">Feels like {temperature.feels_like?.toFixed(1) || 'N/A'}{tempUnit}</div>
        </div>
      </div>

      <div className="weather-stats-grid">
        <div className="weather-stat">
          <div className="stat-icon">💧</div>
          <div className="stat-info">
            <div className="stat-label">Humidity</div>
            <div className="stat-value">{atmosphere.humidity_pct?.toFixed(0) || '0'}%</div>
          </div>
        </div>
        <div className="weather-stat">
          <div className="stat-icon">💨</div>
          <div className="stat-info">
            <div className="stat-label">Wind Speed</div>
            <div className="stat-value">{wind.speed?.toFixed(2) || '0.00'} m/s</div>
          </div>
        </div>
        <div className="weather-stat">
          <div className="stat-icon">🌡️</div>
          <div className="stat-info">
            <div className="stat-label">Pressure</div>
            <div className="stat-value">{atmosphere.pressure_hpa?.toFixed(0) || '0'} hPa</div>
          </div>
        </div>
        <div className="weather-stat">
          <div className="stat-icon">👁️</div>
          <div className="stat-info">
            <div className="stat-label">Visibility</div>
            <div className="stat-value">{result.visibility_m ? (result.visibility_m / 1000).toFixed(1) : '0.0'} km</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ActionButtons({ aqiData, weatherData, onGenerateSummary, loadingCategory }) {
  const actions = [
    {
      title: "Agriculture Consultation",
      description: "Expert advice on crop selection and farming practices",
      icon: "🌾",
      color: "#10b981",
    },
    {
      title: "Health Advisory",
      description: "Personalized health recommendations based on air quality",
      icon: "🏥",
      color: "#3b82f6",
    },
    {
      title: "Air Quality Report",
      description: "Download detailed air quality analysis report",
      icon: "📊",
      color: "#f59e0b",
    },
    {
      title: "Emergency Services",
      description: "Quick access to emergency contacts and services",
      icon: "🚨",
      color: "#ef4444",
    },
  ];

  const handleActionClick = async (category) => {
    if (!aqiData || !weatherData) {
      alert('Please wait for air quality and weather data to load.');
      return;
    }
    await onGenerateSummary(category);
  };

  return (
    <div className="action-buttons-section">
      <h2 className="section-title-main">Quick Actions</h2>
      <div className="action-buttons-grid">
        {actions.map((action, idx) => (
          <button 
            key={idx} 
            className="action-button"
            onClick={() => handleActionClick(action.title)}
            disabled={loadingCategory === action.title}
            style={{ '--action-color': action.color }}
          >
            <div className="action-icon">
              {loadingCategory === action.title ? '⏳' : action.icon}
            </div>
            <div className="action-content">
              <h3 className="action-title">{action.title}</h3>
              <p className="action-description">
                {loadingCategory === action.title ? 'Generating...' : action.description}
              </p>
            </div>
            <div className="action-arrow">→</div>
          </button>
        ))}
      </div>
    </div>
  );
}

function SummaryDisplay({ summary, category, onContinueChat }) {
  const [chatInput, setChatInput] = useState('');
  const [showChatInput, setShowChatInput] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);

  if (!summary || !category) {
    return null;
  }

  const categoryIcons = {
    "Agriculture Consultation": "🌾",
    "Health Advisory": "🏥",
    "Air Quality Report": "📊",
    "Emergency Services": "🚨"
  };

  const categoryColors = {
    "Agriculture Consultation": "#10b981",
    "Health Advisory": "#3b82f6",
    "Air Quality Report": "#f59e0b",
    "Emergency Services": "#ef4444"
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    
    const userQuestion = chatInput;
    setChatLoading(true);
    
    // Add user question to chat history
    setChatHistory(prev => [...prev, { type: 'question', text: userQuestion }]);
    setChatInput('');
    
    // Get AI response
    const response = await onContinueChat(userQuestion);
    
    // Add AI response to chat history if available
    if (response) {
      setChatHistory(prev => [...prev, { type: 'answer', text: response }]);
    }
    
    setChatLoading(false);
  };

  return (
    <div className="summaries-section">
      <h2 className="section-title-main">Generated Summary</h2>
      <div className="summary-single">
        <div className="summary-card" style={{ borderColor: categoryColors[category] || '#6b7280' }}>
          <div className="summary-header" style={{ background: categoryColors[category] || '#6b7280' }}>
            <span className="summary-icon">{categoryIcons[category] || '📄'}</span>
            <h3 className="summary-title">{category}</h3>
          </div>
          <div className="summary-content">
            <p className="summary-text">{summary}</p>
          </div>
          
          {/* Text-to-Speech Controls */}
          <div className="summary-tts">
            <TextToSpeech text={summary} />
          </div>
          
          <div className="summary-actions">
            <button 
              className="continue-chat-btn"
              onClick={() => setShowChatInput(!showChatInput)}
            >
              💬 Continue Chatting
            </button>
          </div>
          
          {showChatInput && (
            <div className="chat-input-section">
              {/* Chat History */}
              {chatHistory.length > 0 && (
                <div className="chat-history">
                  {chatHistory.map((message, index) => (
                    <div 
                      key={index} 
                      className={`chat-message ${message.type === 'question' ? 'user-question' : 'ai-answer'}`}
                    >
                      <div className="message-header">
                        <span className="message-icon">
                          {message.type === 'question' ? '❓' : '🤖'}
                        </span>
                        <span className="message-label">
                          {message.type === 'question' ? 'You asked:' : 'AI Response:'}
                        </span>
                      </div>
                      <p className="message-text">{message.text}</p>
                      
                      {/* Add TTS for AI responses */}
                      {message.type === 'answer' && (
                        <div className="message-tts">
                          <TextToSpeech text={message.text} />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
              
              {/* Chat Input Form */}
              <form onSubmit={handleChatSubmit}>
                <input
                  type="text"
                  className="chat-input"
                  placeholder="Ask a follow-up question..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  disabled={chatLoading}
                />
                <button 
                  type="submit" 
                  className="chat-submit-btn"
                  disabled={chatLoading || !chatInput.trim()}
                >
                  {chatLoading ? '⏳ Sending...' : '📤 Send'}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function LocationBanner({ userLocation, weatherData }) {
  const [isVisible, setIsVisible] = useState(true);

  // Don't render if dismissed
  if (!isVisible) {
    return null;
  }

  const handleClose = () => {
    setIsVisible(false);
  };

  // Don't show banner if still loading
  if (userLocation.loading) {
    return (
      <div className="location-banner loading">
        <span className="location-icon">📍</span>
        <span className="location-text">Detecting your location...</span>
        <button className="location-close" onClick={handleClose} aria-label="Close">
          ✕
        </button>
      </div>
    );
  }

  // Show permission denied message
  if (userLocation.permissionDenied) {
    return (
      <div className="location-banner warning">
        <span className="location-icon">⚠️</span>
        <span className="location-text">
          Location access denied. Showing data for default location (Chennai).
        </span>
        <button className="location-close" onClick={handleClose} aria-label="Close">
          ✕
        </button>
      </div>
    );
  }

  // Show error message
  if (userLocation.error) {
    return (
      <div className="location-banner info">
        <span className="location-icon">ℹ️</span>
        <span className="location-text">{userLocation.error}</span>
        <button className="location-close" onClick={handleClose} aria-label="Close">
          ✕
        </button>
      </div>
    );
  }

  // Show current location
  const locationName = weatherData?.result?.location?.name || 'Your Location';
  const country = weatherData?.result?.location?.country || '';
  
  return (
    <div className="location-banner success">
      <span className="location-icon">📍</span>
      <span className="location-text">
        Showing data for: <strong>{locationName}{country && `, ${country}`}</strong>
        {userLocation.latitude && userLocation.longitude && (
          <span className="location-coords">
            {' '}({userLocation.latitude.toFixed(4)}, {userLocation.longitude.toFixed(4)})
          </span>
        )}
      </span>
      <button className="location-close" onClick={handleClose} aria-label="Close">
        ✕
      </button>
    </div>
  );
}

function TodayView() {
  // Get user's location automatically
  const userLocation = useGeolocation();
  
  // Theme state
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved ? saved === 'dark' : true; // Default to dark mode
  });
  
  const [aqiData, setAqiData] = useState(null);
  const [weatherData, setWeatherData] = useState(null);
  const [aqiLoading, setAqiLoading] = useState(true);
  const [weatherLoading, setWeatherLoading] = useState(true);
  const [aqiError, setAqiError] = useState(null);
  const [weatherError, setWeatherError] = useState(null);
  
  // State for single summary with chat
  const [summary, setSummary] = useState(null);
  const [currentCategory, setCurrentCategory] = useState(null);
  const [chatContext, setChatContext] = useState(null);
  const [loadingCategory, setLoadingCategory] = useState(null);

  // Update theme
  useEffect(() => {
    const root = document.documentElement;
    if (isDarkMode) {
      root.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      root.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDarkMode]);

  const toggleTheme = () => setIsDarkMode(!isDarkMode);

  const fetchAQIData = React.useCallback(async () => {
    setAqiLoading(true);
    setAqiError(null);
    try {
      const params = new URLSearchParams();
      
      // Use user's coordinates if available, otherwise use default city
      if (userLocation.latitude && userLocation.longitude) {
        params.append('lat', userLocation.latitude);
        params.append('lon', userLocation.longitude);
      } else if (!userLocation.loading) {
        // Only use default city if geolocation has finished loading
        params.append('city', 'Chennai');
      } else {
        // Still loading geolocation, wait
        return;
      }
      
      const data = await fetchAPI(`${API_ENDPOINTS.AQI_LATEST}?${params.toString()}`);
      setAqiData(data);
    } catch (err) {
      setAqiError(err.message || 'Failed to fetch AQI data');
    } finally {
      setAqiLoading(false);
    }
  }, [userLocation.latitude, userLocation.longitude, userLocation.loading]);

  const fetchWeatherData = React.useCallback(async () => {
    setWeatherLoading(true);
    setWeatherError(null);
    try {
      const params = new URLSearchParams();
      
      // Use user's coordinates if available, otherwise use default city
      if (userLocation.latitude && userLocation.longitude) {
        params.append('lat', userLocation.latitude);
        params.append('lon', userLocation.longitude);
      } else if (!userLocation.loading) {
        // Only use default city if geolocation has finished loading
        params.append('city', 'Chennai');
      } else {
        // Still loading geolocation, wait
        return;
      }
      
      const data = await fetchAPI(`${API_ENDPOINTS.WEATHER_LATEST}?${params.toString()}`);
      setWeatherData(data);
    } catch (err) {
      setWeatherError(err.message || 'Failed to fetch weather data');
    } finally {
      setWeatherLoading(false);
    }
  }, [userLocation.latitude, userLocation.longitude, userLocation.loading]);

  useEffect(() => {
    // Only fetch data when geolocation is done loading (either success or error)
    if (!userLocation.loading) {
      fetchAQIData();
      fetchWeatherData();
    }
  }, [fetchAQIData, fetchWeatherData, userLocation.loading]);

  // Generate summary for a specific category
  const handleGenerateSummary = React.useCallback(async (category) => {
    setLoadingCategory(category);
    
    try {
      // Extract pollutant data
      const pollutants = aqiData?.results || [];
      const parameters = pollutants
        .filter(p => p.value !== null && p.value !== undefined)
        .map(p => p.pollutant);
      
      const values = {};
      pollutants.forEach(p => {
        if (p.value !== null && p.value !== undefined) {
          values[p.pollutant] = p.value;
        }
      });
      
      // Get location info
      const location = weatherData?.result?.location;
      const locationName = location?.name && location?.country 
        ? `${location.name}, ${location.country}` 
        : 'Unknown location';
      
      // Get weather data
      const weather = weatherData?.result || {};
      const weatherInfo = {
        temperature: weather.temperature?.value,
        humidity: weather.atmosphere?.humidity_pct,
        wind_speed: weather.wind?.speed,
        pressure: weather.atmosphere?.pressure_hpa,
        description: weather.conditions?.description
      };
      
      // Make API call
      const response = await fetch(API_ENDPOINTS.GENERATE_REPORT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          categories: [{
            category: category,
            parameters: parameters,
            values: values,
            aqi: aqiData?.aqi || 0,
            location: locationName,
            weather: weatherInfo
          }]
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success && data.summary) {
        // Replace the current summary with new one
        setSummary(data.summary);
        setCurrentCategory(data.category || category);
        setChatContext(data.context);
      } else {
        throw new Error(data.error || 'Failed to generate summary');
      }
    } catch (error) {
      console.error('Error generating summary:', error);
      alert(`Failed to generate ${category}: ${error.message}`);
    } finally {
      setLoadingCategory(null);
    }
  }, [aqiData, weatherData]);

  // Handle follow-up chat questions
  const handleContinueChat = React.useCallback(async (question) => {
    try {
      // Extract current data
      const pollutants = aqiData?.results || [];
      const parameters = pollutants
        .filter(p => p.value !== null && p.value !== undefined)
        .map(p => p.pollutant);
      
      const values = {};
      pollutants.forEach(p => {
        if (p.value !== null && p.value !== undefined) {
          values[p.pollutant] = p.value;
        }
      });
      
      const location = weatherData?.result?.location;
      const locationName = location?.name && location?.country 
        ? `${location.name}, ${location.country}` 
        : 'Unknown location';
      
      const weather = weatherData?.result || {};
      const weatherInfo = {
        temperature: weather.temperature?.value,
        humidity: weather.atmosphere?.humidity_pct,
        wind_speed: weather.wind?.speed,
        pressure: weather.atmosphere?.pressure_hpa,
        description: weather.conditions?.description
      };
      
      // Make API call with follow-up question
      const response = await fetch(API_ENDPOINTS.GENERATE_REPORT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          categories: [{
            category: currentCategory,
            parameters: parameters,
            values: values,
            aqi: aqiData?.aqi || 0,
            location: locationName,
            weather: weatherInfo
          }],
          follow_up_question: question,
          previous_context: chatContext
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success && data.summary) {
        // Update context for future questions
        setChatContext(data.context);
        // Return the response for chat history
        return data.summary;
      } else {
        throw new Error(data.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Error in chat:', error);
      alert(`Failed to get response: ${error.message}`);
      return null;
    }
  }, [aqiData, weatherData, currentCategory, chatContext]);

  const themeValue = { isDarkMode, toggleTheme };

  return (
    <ThemeContext.Provider value={themeValue}>
      <div className="today-view-redesign">
        {/* Navigation Bar */}
        <Navbar isDarkMode={isDarkMode} toggleTheme={toggleTheme} />
        
        <div className="content-wrapper">
          <LocationBanner userLocation={userLocation} weatherData={weatherData} />
          
          <div className="dashboard-grid">
            <AQICard aqiData={aqiData} loading={aqiLoading} error={aqiError} />
            <WeatherCard weatherData={weatherData} loading={weatherLoading} error={weatherError} />
          </div>
          
          <ActionButtons 
            aqiData={aqiData}
            weatherData={weatherData}
            onGenerateSummary={handleGenerateSummary}
            loadingCategory={loadingCategory}
          />
          
          <SummaryDisplay 
            summary={summary} 
            category={currentCategory}
            onContinueChat={handleContinueChat}
          />
        </div>
      </div>
    </ThemeContext.Provider>
  );
}

export default TodayView;
