// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API Endpoints
export const API_ENDPOINTS = {
  AQI_LATEST: `${API_BASE_URL}/api/aqi/latest/`,
  WEATHER_LATEST: `${API_BASE_URL}/api/weather/latest/`,
  PREDICT_AQI: `${API_BASE_URL}/api/aqi/predict/`,
  GENERATE_REPORT: `${API_BASE_URL}/api/generate-report/`,
};

// Helper function to fetch data
export const fetchAPI = async (url, options = {}) => {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};
