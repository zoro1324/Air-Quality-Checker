// useGeolocation.js - Custom hook for browser geolocation

import { useState, useEffect } from 'react';

/**
 * Custom hook to get user's current location using browser Geolocation API
 * @returns {Object} - { latitude, longitude, city, loading, error, permissionDenied }
 */
const useGeolocation = () => {
  const [location, setLocation] = useState({
    latitude: null,
    longitude: null,
    city: null,
    loading: true,
    error: null,
    permissionDenied: false,
  });

  useEffect(() => {
    // Check if geolocation is supported
    if (!navigator.geolocation) {
      setLocation(prev => ({
        ...prev,
        loading: false,
        error: 'Geolocation is not supported by your browser',
      }));
      return;
    }

    // Request user's location
    navigator.geolocation.getCurrentPosition(
      // Success callback
      (position) => {
        const { latitude, longitude } = position.coords;
        
        setLocation({
          latitude,
          longitude,
          city: null, // City name will be fetched from API response
          loading: false,
          error: null,
          permissionDenied: false,
        });
      },
      // Error callback
      (error) => {
        let errorMessage = 'Unable to retrieve your location';
        let isDenied = false;

        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Location permission denied. Using default location.';
            isDenied = true;
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Location information unavailable. Using default location.';
            break;
          case error.TIMEOUT:
            errorMessage = 'Location request timed out. Using default location.';
            break;
          default:
            errorMessage = 'An unknown error occurred. Using default location.';
        }

        setLocation({
          latitude: null,
          longitude: null,
          city: null,
          loading: false,
          error: errorMessage,
          permissionDenied: isDenied,
        });
      },
      // Options
      {
        enableHighAccuracy: true,
        timeout: 10000, // 10 seconds
        maximumAge: 300000, // Cache position for 5 minutes
      }
    );
  }, []);

  return location;
};

export default useGeolocation;
