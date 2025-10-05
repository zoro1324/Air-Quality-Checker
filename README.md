# Air-Quality-Checker

## Project Description

Air Quality Checker is a comprehensive web application designed to monitor and predict air quality in real-time. Built for the NASA Space Apps Challenge, this project provides users with accurate air quality data and predictions to help them make informed decisions about their health and outdoor activities.

### Key Features

- **Real-time Air Quality Monitoring**: Track current air quality conditions based on your location
- **AQI Predictions**: Machine learning-powered predictions for future air quality levels
- **Geospatial Analysis**: Utilizes PostGIS for accurate location-based air quality queries
- **Interactive Dashboard**: Visual representation of air quality data with charts and color-coded indicators
- **Voice Accessibility**: Text-to-speech and voice input features for enhanced accessibility
- **Historical Data**: View and analyze historical air quality trends
- **Multi-language Support**: Available in English, Tamil, and Hindi
- **Responsive Design**: Optimized for both desktop and mobile devices

### Technology Stack

**Frontend:**
- React with Vite for fast, modern UI development
- Chart.js for data visualization
- Geolocation API for automatic location detection
- Accessibility features including TTS and voice input

**Backend:**
- Django 5 REST API
- GeoDjango with PostGIS for geospatial queries
- PostgreSQL database with PostGIS extension
- Machine learning model for AQI predictions (TensorFlow/Keras)

**Data:**
- Air quality measurements including PM2.5, PM10, NO2, SO2, CO, and O3
- Location-based data with latitude/longitude and geometry points

## Overview

Backend is Django 5 with a REST API, frontend is Vite + React. The backend now supports PostGIS for geospatial queries using GeoDjango.

## Team

Our team consists of 6 members working on different aspects of the project:

### Backend Team
- **Naveemkumar** - Backend Developer
- **Sarah Jeslyn** - Backend Developer
- **Parthiv** - Backend Developer

### Frontend Team
- **Nisha** - Frontend Developer
- **Ramvignesh** - Frontend Developer
- **Lakshya** - Frontend Developer

## Backend database: PostGIS setup

You can run with SQLite temporarily by setting `USE_SQLITE=True` in `backend/.env`, but to use geospatial features switch to PostGIS.

### Install PostgreSQL + PostGIS (Windows)

- Install PostgreSQL via EnterpriseDB installer. In StackBuilder, add the PostGIS extension matching your version.
- Or use a package manager:
	- Chocolatey: `choco install postgresql` then install PostGIS via StackBuilder.
	- Scoop: `scoop install postgresql` (PostGIS via StackBuilder separately).

### Create database and enable PostGIS

In psql or pgAdmin:

1. CREATE DATABASE air_quality;
2. \c air_quality
3. CREATE EXTENSION IF NOT EXISTS postgis;

### Configure environment

1. Copy `backend/.env.example` to `backend/.env`.
2. Set DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT.
3. Ensure `USE_SQLITE=False` (default).

### Install deps and migrate

From `backend/` directory:

1. Create a venv and install requirements.
2. Run `python manage.py migrate`. The migration will:
	 - Ensure PostGIS extension exists (if permissions allow)
	 - Add `geom` PointField to `api_location`
	 - Backfill `geom` from `latitude`/`longitude`

If extension creation fails due to permissions, create it once with a superuser and rerun migrations.

### Notes

- GeoDjango needs GDAL/GEOS libraries. On Windows, these come with the PostGIS installer; ensure binaries are in PATH.
- The API keeps `latitude`/`longitude` for compatibility. New geospatial queries should use the `geom` field.