# Air-Quality-Checker

## Overview

Backend is Django 5 with a REST API, frontend is Vite + React. The backend now supports PostGIS for geospatial queries using GeoDjango.

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