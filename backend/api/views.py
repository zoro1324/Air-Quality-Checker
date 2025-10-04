from rest_framework.decorators import api_view
from rest_framework.response import Response
from openaq import OpenAQ
import decouple
from .models import Location, Measurement
import google.generativeai as genai
from .serializers import (
    PredictAQIQuerySerializer,
    PredictAQIResponseSerializer,
    GenerateReportRequestSerializer,
    GenerateReportResponseSerializer,
)
from django.contrib.gis.geos import Point
import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
from datetime import datetime, timedelta, timezone
import math
from typing import Optional, Tuple, List
import os



# --- Optional TensorFlow model cache ---
_aqi_model = None
_aqi_model_path = None
_aqi_model_error = None

def _get_aqi_model():
    global _aqi_model, _aqi_model_path, _aqi_model_error
    if _aqi_model is not None:
        return _aqi_model, None
    try:
        # Lazy import TensorFlow/Keras
        from tensorflow.keras.models import load_model  # type: ignore
        # Model path relative to backend directory (../Models/AQI_prediction_model.h5)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
        model_path = os.path.abspath(os.path.join(base_dir, '..', 'Models', 'AQI_prediction_model.h5'))
        _aqi_model_path = model_path
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
        _aqi_model = load_model(model_path)
        return _aqi_model, None
    except Exception as e:
        _aqi_model_error = str(e)
        return None, _aqi_model_error

# Create your views here.

@api_view(['GET'])
def latest_measurements(request):
    # Use OpenWeather Air Pollution API instead of OpenAQ
    api_key = decouple.config("OPENWEATHER_API", default=None) or decouple.config("OPENWHEATHER_API", default=None)
    if not api_key:
        return Response({"error": "OpenWeather API key missing. Set OPENWEATHER_API in backend/.env"}, status=500)

    # Accept lat/lon or city query; default to Chennai, IN
    # Validate query params via serializer
    query_serializer = PredictAQIQuerySerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({'error': 'Invalid query parameters', 'details': query_serializer.errors}, status=400)

    q_city = query_serializer.validated_data.get('q') or query_serializer.validated_data.get('city')
    lat_param = query_serializer.validated_data.get('lat')
    lon_param = query_serializer.validated_data.get('lon')
    default_lat, default_lon = 13.0827, 80.2707

    # Resolve coordinates
    lat_val = None
    lon_val = None
    try:
        if lat_param is not None and lon_param is not None:
            lat_val = float(lat_param)
            lon_val = float(lon_param)
        elif q_city:
            # Geocode city to coordinates
            geo_endpoint = 'https://api.openweathermap.org/geo/1.0/direct'
            geo_params = {'q': q_city, 'limit': 1, 'appid': api_key}
            geo_url = f"{geo_endpoint}?{urlencode(geo_params)}"
            try:
                req = Request(geo_url, headers={"User-Agent": "AirQualityChecker/1.0"})
                with urlopen(req, timeout=10) as resp:
                    geo_body = resp.read().decode('utf-8')
                geo_data = json.loads(geo_body)
            except HTTPError as e:
                try:
                    err_json = json.loads(e.read().decode('utf-8'))
                except Exception:
                    err_json = {"message": str(e)}
                return Response({"error": "Geocoding failed", "details": err_json}, status=e.code if 400 <= e.code < 600 else 502)
            except URLError as e:
                return Response({"error": f"Failed to reach OpenWeather Geocoding: {e.reason}"}, status=502)
            except Exception:
                return Response({"error": "Invalid Geocoding response"}, status=502)

            if not geo_data:
                return Response({"error": "City not found"}, status=404)
            lat_val = float(geo_data[0].get('lat'))
            lon_val = float(geo_data[0].get('lon'))
        else:
            lat_val = default_lat
            lon_val = default_lon
    except ValueError:
        return Response({"error": "lat and lon must be valid numbers"}, status=400)

    # Fetch air pollution data
    air_endpoint = 'https://api.openweathermap.org/data/2.5/air_pollution'
    air_params = {'lat': lat_val, 'lon': lon_val, 'appid': api_key}
    air_url = f"{air_endpoint}?{urlencode(air_params)}"

    try:
        req = Request(air_url, headers={"User-Agent": "AirQualityChecker/1.0"})
        with urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
    except HTTPError as e:
        try:
            err_json = json.loads(e.read().decode('utf-8'))
        except Exception:
            err_json = {"message": str(e)}
        return Response({"error": "OpenWeather Air Pollution API error", "details": err_json}, status=e.code if 400 <= e.code < 600 else 502)
    except URLError as e:
        return Response({"error": f"Failed to reach OpenWeather: {e.reason}"}, status=502)

    try:
        data = json.loads(body)
    except Exception:
        return Response({"error": "Invalid JSON from OpenWeather"}, status=502)

    lst = data.get('list') or []
    first = lst[0] if lst else {}
    main = first.get('main', {}) or {}
    comps = first.get('components', {}) or {}
    dt = first.get('dt')

    # Map OpenWeather component keys to human-friendly pollutant names
    key_name = [
        ('co', 'CO'),
        ('no', 'NO'),
        ('no2', 'NO₂'),
        ('o3', 'O₃'),
        ('so2', 'SO₂'),
        ('pm2_5', 'PM2.5'),
        ('pm10', 'PM10'),
        ('nh3', 'NH₃'),
    ]

    results = []
    for key, label in key_name:
        results.append({
            'pollutant': label,
            'key': key,
            'value': comps.get(key),
            'units': 'μg/m³',
        })

    count = sum(1 for r in results if r['value'] is not None)

    return Response({
        'message': 'Latest air pollution from OpenWeather',
        'coordinates': {'lat': lat_val, 'lon': lon_val},
        'aqi': main.get('aqi'),
        'timestamp_utc': dt,
        'count': count,
        'results': results,
    })


@api_view(['GET'])
def instert_data(request):
    OPENAQ_API = decouple.config("OPENAQ_API")
    client = OpenAQ(OPENAQ_API)
    page = 1
    limit = 100
    inserted_count = 0

    while True:
        response = client.locations.list(
            bbox=(76.1667, 7.9119, 80.8167, 13.6453),
            limit=limit,
            page=page
        )
        # OpenAQ SDK may return a list, or an object with a .results list
        locations = getattr(response, 'results', None)
        if locations is None:
            locations = response if isinstance(response, list) else []
        if not locations:
            break

        for loc in locations:
            # Safely extract attributes since OpenAQ SDK objects may vary by version
            loc_id = getattr(loc, 'id', None)
            if loc_id is None and isinstance(loc, dict):
                loc_id = loc.get('id') or loc.get('locationId') or loc.get('location_id')
            if loc_id is None:
                # If we can't determine an ID, skip this record to avoid integrity errors
                continue

            # Coordinates can be nested or flat depending on SDK
            latitude = None
            longitude = None
            coords = getattr(loc, 'coordinates', None) or getattr(loc, 'coord', None)
            if coords is not None:
                if isinstance(coords, dict):
                    latitude = coords.get('latitude') or coords.get('lat')
                    longitude = coords.get('longitude') or coords.get('lon')
                else:
                    latitude = getattr(coords, 'latitude', None)
                    if latitude is None:
                        latitude = getattr(coords, 'lat', None)
                    longitude = getattr(coords, 'longitude', None)
                    if longitude is None:
                        longitude = getattr(coords, 'lon', None)
            else:
                # Fallback if lat/lon are top-level
                if isinstance(loc, dict):
                    latitude = loc.get('latitude') or loc.get('lat')
                    longitude = loc.get('longitude') or loc.get('lon')
                else:
                    latitude = getattr(loc, 'latitude', getattr(loc, 'lat', None))
                    longitude = getattr(loc, 'longitude', getattr(loc, 'lon', None))

            # Build geometry point if lat/lon available (x=lon, y=lat)
            geom = None
            if latitude is not None and longitude is not None:
                try:
                    geom = Point(float(longitude), float(latitude), srid=4326)
                except Exception:
                    geom = None

            Location.objects.update_or_create(
                location_id=loc_id,
                defaults={
                    # Model stores geometry in two PointFields named 'latitude' and 'longitude'
                    # (schema could be improved later to a single 'location' field)
                    'latitude': geom,
                    'longitude': geom,
                }
            )
            inserted_count += 1

        page += 1

    return Response({"message": f"Inserted/Updated {inserted_count} locations successfully"})

@api_view(['GET'])
def latest_weather(request):
    # Get API key from env; accept either OPENWEATHER_API (correct) or OPENWHEATHER_API (legacy)
    api_key = decouple.config("OPENWEATHER_API", default=None)
    if not api_key:
        # Backward-compat: typo variant in .env
        api_key = decouple.config("OPENWHEATHER_API", default=None)

    if not api_key:
        return Response({
            "error": "OpenWeather API key missing. Set OPENWEATHER_API in backend/.env",
        }, status=500)

    # Parse query params
    q_city = request.query_params.get('q') or request.query_params.get('city')
    lat = request.query_params.get('lat')
    lon = request.query_params.get('lon')
    units = request.query_params.get('units', 'metric')

    # Default to Chennai, IN if no coords/city provided
    default_lat, default_lon = 13.0827, 80.2707

    params = {
        'appid': api_key,
        'units': units if units in ('standard', 'metric', 'imperial') else 'metric',
    }

    endpoint = 'https://api.openweathermap.org/data/2.5/weather'

    # Build request params based on precedence: lat/lon > city > default
    try:
        if lat is not None and lon is not None:
            params['lat'] = float(lat)
            params['lon'] = float(lon)
        elif q_city:
            params['q'] = q_city
        else:
            params['lat'] = default_lat
            params['lon'] = default_lon
    except ValueError:
        return Response({"error": "lat and lon must be valid numbers"}, status=400)

    url = f"{endpoint}?{urlencode(params)}"
    try:
        req = Request(url, headers={"User-Agent": "AirQualityChecker/1.0"})
        with urlopen(req, timeout=10) as resp:
            status = getattr(resp, 'status', 200)
            body = resp.read().decode('utf-8')
    except HTTPError as e:
        # Attempt to read error body json
        try:
            err_body = e.read().decode('utf-8')
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"message": str(e)}
        return Response({
            "error": "OpenWeather API error",
            "status_code": e.code,
            "details": err_json,
        }, status=e.code if 400 <= e.code < 600 else 502)
    except URLError as e:
        return Response({"error": f"Failed to reach OpenWeather: {e.reason}"}, status=502)

    try:
        data = json.loads(body)
    except Exception:
        return Response({"error": "Invalid JSON from OpenWeather"}, status=502)

    # Curate a compact, frontend-friendly payload
    coord = data.get('coord', {}) or {}
    main = data.get('main', {}) or {}
    wind = data.get('wind', {}) or {}
    sys = data.get('sys', {}) or {}
    weather_list = data.get('weather') or []
    weather0 = weather_list[0] if weather_list else {}

    curated = {
        'location': {
            'name': data.get('name'),
            'country': sys.get('country'),
        },
        'coordinates': {
            'lat': coord.get('lat'),
            'lon': coord.get('lon'),
        },
        'conditions': {
            'main': weather0.get('main'),
            'description': weather0.get('description'),
            'icon': weather0.get('icon'),
        },
        'temperature': {
            'value': main.get('temp'),
            'feels_like': main.get('feels_like'),
            'min': main.get('temp_min'),
            'max': main.get('temp_max'),
            'units': params['units'],
        },
        'atmosphere': {
            'pressure_hpa': main.get('pressure'),
            'humidity_pct': main.get('humidity'),
        },
        'wind': {
            'speed': wind.get('speed'),
            'deg': wind.get('deg'),
            'gust': wind.get('gust'),
        },
        'visibility_m': data.get('visibility'),
        'timestamp_utc': data.get('dt'),
        'sunrise_utc': sys.get('sunrise'),
        'sunset_utc': sys.get('sunset'),
        'raw': data,  # Keep raw for debugging/extended use; remove if not needed
    }

    return Response({
        "message": "Latest current weather from OpenWeather",
        "query": {k: v for k, v in params.items() if k != 'appid'},
        "result": curated,
    })

@api_view(['GET'])
def predict_aqi(request):
    """
    Predict AQI for a specified period at a given coordinate/city.

    Query params:
      - lat, lon: coordinates (preferred)
      - q or city: city name to geocode via OpenWeather
      - start, end: Unix seconds or ISO-8601 timestamps in UTC (e.g. 2025-10-04T00:00:00Z)
      - hours: integer hours lookback if start/end not provided (default: 24)
    Behavior:
      - Chooses nearest Location.location_id from DB to the resolved lat/lon
      - Fetches OpenWeather Air Pollution history for [start,end]
      - If TensorFlow model Models/AQI_prediction_model.h5 is available, outputs model predictions
      - Always returns OpenWeather components and their AQI as baseline
    """

    # 1) Resolve coordinates from lat/lon or city query
    api_key = decouple.config("OPENWEATHER_API", default=None) or decouple.config("OPENWHEATHER_API", default=None)
    if not api_key:
        return Response({"error": "OpenWeather API key missing. Set OPENWEATHER_API in backend/.env"}, status=500)

    # Validate query params via serializer
    query_serializer = PredictAQIQuerySerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({'error': 'Invalid query parameters', 'details': query_serializer.errors}, status=400)

    q_city = query_serializer.validated_data.get('q') or query_serializer.validated_data.get('city')
    lat_param = query_serializer.validated_data.get('lat')
    lon_param = query_serializer.validated_data.get('lon')
    default_lat, default_lon = 13.0827, 80.2707  # Chennai fallback

    try:
        if lat_param is not None and lon_param is not None:
            lat_val = float(lat_param)
            lon_val = float(lon_param)
        elif q_city:
            # Geocode city
            geo_endpoint = 'https://api.openweathermap.org/geo/1.0/direct'
            geo_params = {'q': q_city, 'limit': 1, 'appid': api_key}
            geo_url = f"{geo_endpoint}?{urlencode(geo_params)}"
            try:
                req = Request(geo_url, headers={"User-Agent": "AirQualityChecker/1.0"})
                with urlopen(req, timeout=10) as resp:
                    geo_body = resp.read().decode('utf-8')
                geo_data = json.loads(geo_body)
                if not geo_data:
                    return Response({"error": "City not found"}, status=404)
                lat_val = float(geo_data[0].get('lat'))
                lon_val = float(geo_data[0].get('lon'))
            except HTTPError as e:
                try:
                    err_json = json.loads(e.read().decode('utf-8'))
                except Exception:
                    err_json = {"message": str(e)}
                return Response({"error": "Geocoding failed", "details": err_json}, status=e.code if 400 <= e.code < 600 else 502)
            except URLError as e:
                return Response({"error": f"Failed to reach OpenWeather Geocoding: {e.reason}"}, status=502)
        else:
            lat_val = default_lat
            lon_val = default_lon
    except ValueError:
        return Response({"error": "lat and lon must be valid numbers"}, status=400)

    # 2) Parse time range
    def parse_ts(val: Optional[str]) -> Optional[int]:
        if not val:
            return None
        # Accept Unix seconds or ISO-8601 (UTC)
        try:
            # numeric seconds
            return int(float(val))
        except ValueError:
            pass
        try:
            dt = datetime.fromisoformat(val.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except Exception:
            return None

    now_utc = datetime.now(timezone.utc)
    start_q = query_serializer.validated_data.get('start')
    end_q = query_serializer.validated_data.get('end')
    hours_q = query_serializer.validated_data.get('hours')

    start_ts = parse_ts(start_q)
    end_ts = parse_ts(end_q)

    if start_ts is None or end_ts is None:
        try:
            lookback_h = int(hours_q) if hours_q is not None else 24
        except ValueError:
            lookback_h = 24
        end_ts = int(now_utc.timestamp())
        start_ts = int((now_utc - timedelta(hours=lookback_h)).timestamp())

    if end_ts <= start_ts:
        return Response({"error": "end must be greater than start"}, status=400)

    # 3) Choose nearest Location from DB
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000.0  # meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    # Fallback to Python-side distance to avoid requiring PostGIS features at runtime
    locations = list(Location.objects.all().only('location_id', 'latitude', 'longitude', 'geom'))
    if not locations:
        return Response({"error": "No locations found. Load locations first via /api/aqi/insert/."}, status=404)

    nearest_loc_id: Optional[int] = None
    nearest_dist: float = float('inf')
    for loc in locations:
        lat2 = None
        lon2 = None
        try:
            if getattr(loc, 'geom', None):
                # GeoDjango Point: x=lon, y=lat
                lon2 = float(loc.geom.x)
                lat2 = float(loc.geom.y)
            else:
                lat2 = float(loc.latitude) if loc.latitude is not None else None
                lon2 = float(loc.longitude) if loc.longitude is not None else None
        except Exception:
            lat2 = lon2 = None
        if lat2 is None or lon2 is None:
            continue
        d = haversine(lat_val, lon_val, lat2, lon2)
        if d < nearest_dist:
            nearest_dist = d
            nearest_loc_id = loc.location_id

    if nearest_loc_id is None:
        return Response({"error": "Could not resolve nearest location from DB coordinates."}, status=404)

    # 4) Fetch Air Pollution history from OpenWeather
    hist_endpoint = 'https://api.openweathermap.org/data/2.5/air_pollution/history'
    hist_params = {
        'lat': lat_val,
        'lon': lon_val,
        'start': start_ts,
        'end': end_ts,
        'appid': api_key,
    }
    hist_url = f"{hist_endpoint}?{urlencode(hist_params)}"
    try:
        req = Request(hist_url, headers={"User-Agent": "AirQualityChecker/1.0"})
        with urlopen(req, timeout=15) as resp:
            body = resp.read().decode('utf-8')
    except HTTPError as e:
        try:
            err_json = json.loads(e.read().decode('utf-8'))
        except Exception:
            err_json = {"message": str(e)}
        return Response({"error": "OpenWeather Air Pollution history error", "details": err_json}, status=e.code if 400 <= e.code < 600 else 502)
    except URLError as e:
        return Response({"error": f"Failed to reach OpenWeather: {e.reason}"}, status=502)

    try:
        hist = json.loads(body)
    except Exception:
        return Response({"error": "Invalid JSON from OpenWeather history"}, status=502)

    items = hist.get('list') or []

    # 5) Prepare features and optionally run model predictions
    # Feature order assumption (match training):
    feature_keys = ['co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']

    X: List[List[float]] = []
    rows_meta: List[dict] = []
    for it in items:
        comps = it.get('components', {}) or {}
        row = [float(comps.get(k)) if comps.get(k) is not None else float('nan') for k in feature_keys]
        # Skip rows with missing components for prediction; still include in output with predicted_aqi=None
        if all(not math.isnan(v) for v in row):
            X.append(row)
            rows_meta.append({'dt': it.get('dt'), 'components': comps, 'aqi': (it.get('main') or {}).get('aqi')})
        else:
            rows_meta.append({'dt': it.get('dt'), 'components': comps, 'aqi': (it.get('main') or {}).get('aqi'), 'skip': True})

    predictions_scalar: List[Optional[float]] = []  # For single-output (AQI)
    predictions_vector: List[Optional[List[float]]] = []  # For multi-output (per pollutant)
    model_loaded = False
    model_err: Optional[str] = None
    if X:
        model, model_err = _get_aqi_model()
        if model is not None:
            try:
                import numpy as np
                X_np = np.array(X, dtype=float)
                y_pred = model.predict(X_np, verbose=0)
                model_loaded = True
                # Handle shapes: (n,1) -> scalar AQI; (n,k) -> per-pollutant vectors
                if hasattr(y_pred, 'shape') and len(y_pred.shape) == 2:
                    n, m = y_pred.shape[0], y_pred.shape[1]
                    if m == 1:
                        predictions_scalar = y_pred.reshape(-1).tolist()
                        predictions_vector = [None] * n
                    elif m == len(feature_keys):
                        predictions_vector = y_pred.tolist()
                        predictions_scalar = [None] * n
                    else:
                        # Unknown output size: return raw values as vector
                        predictions_vector = y_pred.tolist()
                        predictions_scalar = [None] * y_pred.shape[0]
                else:
                    # Fallback: attempt to flatten
                    y_flat = np.array(y_pred).reshape(-1).tolist()
                    predictions_scalar = y_flat
                    predictions_vector = []
            except Exception as e:
                model_err = str(e)
                predictions_scalar = []
                predictions_vector = []

    # 6) Build response aligning predictions back to timeline
    pred_scalar_iter = iter(predictions_scalar)
    pred_vector_iter = iter(predictions_vector)
    results = []
    for meta in rows_meta:
        dt = meta.get('dt')
        comps = meta.get('components') or {}
        aqi = meta.get('aqi')
        if meta.get('skip'):
            pred_val = None
            pred_vec = None
        else:
            try:
                pred_val = next(pred_scalar_iter) if model_loaded and predictions_scalar else None
            except StopIteration:
                pred_val = None
            try:
                pred_vec = next(pred_vector_iter) if model_loaded and predictions_vector else None
            except StopIteration:
                pred_vec = None
        item = {
            'timestamp_utc': dt,
            'components': {k: comps.get(k) for k in feature_keys},
            'openweather_aqi': aqi,
            'predicted_aqi': pred_val,
        }
        if pred_vec is not None:
            # Map vector outputs back to feature keys when sizes align
            if isinstance(pred_vec, list) and len(pred_vec) == len(feature_keys):
                item['predicted_components'] = {k: (pred_vec[i] if i < len(pred_vec) else None) for i, k in enumerate(feature_keys)}
            else:
                item['prediction_raw'] = pred_vec
        results.append(item)

    response_payload = {
        'message': 'AQI predictions',
        'coordinates': {'lat': lat_val, 'lon': lon_val},
        'location': {'nearest_location_id': nearest_loc_id, 'distance_m': None if math.isinf(nearest_dist) else round(nearest_dist, 2)},
        'time_range': {'start_utc': start_ts, 'end_utc': end_ts},
        'feature_order': feature_keys,
        'model': {'loaded': model_loaded, 'error': model_err},
        'count': len(results),
        'results': results,
    }
    
    # Generate AI summary if requested
    generate_summary = request.query_params.get('generate_summary', '').lower() == 'true'
    print(f"Generate summary requested: {generate_summary}, Results count: {len(results)}")
    if generate_summary and results:
        try:
            # Calculate average predicted AQI (fallback to openweather_aqi if model predictions not available)
            predicted_aqis = [
                r.get('predicted_aqi') or r.get('openweather_aqi') 
                for r in results 
                if (r.get('predicted_aqi') is not None or r.get('openweather_aqi') is not None)
            ]
            avg_aqi = sum(predicted_aqis) / len(predicted_aqis) if predicted_aqis else None
            print(f"Calculated average AQI: {avg_aqi}, from {len(predicted_aqis)} data points")
            
            # Calculate average pollutants
            avg_pollutants = {}
            for key in feature_keys:
                values = [r['components'].get(key) for r in results if r['components'].get(key) is not None]
                if values:
                    avg_pollutants[key] = sum(values) / len(values)
            
            # Determine time period description
            time_diff_hours = (end_ts - start_ts) / 3600
            if time_diff_hours <= 24:
                period_desc = "next 24 hours"
            elif time_diff_hours <= 168:  # 7 days
                period_desc = f"next {int(time_diff_hours / 24)} days"
            else:
                period_desc = f"next {int(time_diff_hours / 168)} weeks"
            
            # Generate AI summary for predictions
            genai.configure(api_key=decouple.config("GEMINI_API_KEY", default=""))
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            pollutant_info = ", ".join([f"{k}: {v:.2f} μg/m³" for k, v in avg_pollutants.items()])
            
            # Format AQI value properly
            aqi_display = f"{avg_aqi:.1f}" if avg_aqi is not None else "N/A"
            
            prompt = f"""Based on air quality predictions for the {period_desc}:

Location: Coordinates ({lat_val}, {lon_val})
Time Period: {period_desc}
Average Predicted AQI: {aqi_display}
Average Pollutant Levels: {pollutant_info}

Provide a comprehensive 5-6 sentence summary including:

1. **Long-term Health Advisory**: Health recommendations for the predicted period, who should take precautions
2. **Agricultural Planning**: Specific crop recommendations for farmers based on predicted air quality trends
3. **Activity Planning**: Best times for outdoor activities during this period
4. **Trend Analysis**: Whether air quality is expected to improve or worsen
5. **Actionable Recommendations**: Practical steps people should take based on predictions

Make it practical, forward-looking, and actionable for long-term planning."""

            response = model.generate_content(prompt)
            print(f"Generated AI summary successfully")
            response_payload['ai_summary'] = {
                'summary': response.text.strip(),
                'period': period_desc,
                'avg_predicted_aqi': avg_aqi,
                'avg_pollutants': avg_pollutants
            }
        except Exception as e:
            print(f"Error generating AI summary: {str(e)}")
            response_payload['ai_summary'] = {
                'error': f"Failed to generate summary: {str(e)}"
            }

    # Validate/format output via serializer
    resp_ser = PredictAQIResponseSerializer(data=response_payload)
    if not resp_ser.is_valid():
        # If our own output schema mismatches, still return the raw payload with a warning
        response_payload['warning'] = {'serializer_errors': resp_ser.errors}
        return Response(response_payload)
    return Response(resp_ser.data)

@api_view(['POST'])
def prediction_followup(request):
    """
    Handle follow-up questions specifically for prediction summaries.
    
    Expected POST body:
    {
        "question": "What crops are best for these conditions?",
        "prediction_context": {
            "period": "next 7 days",
            "avg_predicted_aqi": 85,
            "avg_pollutants": {...},
            "summary": "Previous AI summary..."
        }
    }
    """
    try:
        question = request.data.get('question', '').strip()
        prediction_context = request.data.get('prediction_context', {})
        
        if not question:
            return Response({
                "success": False,
                "error": "Question is required"
            }, status=400)
        
        if not prediction_context:
            return Response({
                "success": False,
                "error": "Prediction context is required"
            }, status=400)
        
        # Extract context information
        period = prediction_context.get('period', 'the predicted period')
        avg_aqi = prediction_context.get('avg_predicted_aqi', 'N/A')
        avg_pollutants = prediction_context.get('avg_pollutants', {})
        previous_summary = prediction_context.get('summary', '')
        
        # Format pollutant information
        pollutant_info = ", ".join([f"{k}: {v:.2f} μg/m³" for k, v in avg_pollutants.items()])
        
        # Format AQI display
        aqi_display = f"{avg_aqi:.1f}" if isinstance(avg_aqi, (int, float)) else str(avg_aqi)
        
        # Initialize Gemini
        genai.configure(api_key=decouple.config("GEMINI_API_KEY", default=""))
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Build comprehensive prompt with prediction context
        prompt = f"""You are an air quality expert providing advice based on PREDICTED air quality data.

PREDICTION CONTEXT:
- Time Period: {period}
- Average Predicted AQI: {aqi_display}
- Average Pollutant Levels: {pollutant_info}

PREVIOUS ANALYSIS:
{previous_summary}

USER QUESTION:
{question}

Provide a detailed, actionable 4-5 sentence response that:
1. Directly answers the user's question
2. References the specific predicted time period ({period})
3. Considers the predicted AQI level ({aqi_display})
4. Provides practical recommendations for planning ahead
5. Is specific and actionable (avoid generic advice)

Remember: This is PREDICTED data for future planning, not current conditions."""
        
        try:
            response = model.generate_content(prompt)
            answer_text = response.text.strip()
            
            return Response({
                "success": True,
                "answer": answer_text,
                "question": question
            })
            
        except Exception as ai_error:
            return Response({
                "success": False,
                "error": f"AI processing error: {str(ai_error)}"
            }, status=500)
        
    except Exception as e:
        return Response({
            "success": False,
            "error": f"Failed to process follow-up: {str(e)}"
        }, status=500)

@api_view(['POST'])
def generate_report(request):
    """
    Generate AI-powered summaries for air quality report categories with weather context.
    
    Expected POST body:
    {
        "categories": [
            {
                "category": "Agriculture Consultation",
                "parameters": ["PM2.5", "PM10", "O3"],
                "values": {
                    "PM2.5": 35.5,
                    "PM10": 78.2,
                    "O3": 45.1
                },
                "aqi": 85,
                "location": "Chennai, IN",
                "weather": {
                    "temperature": 23.1,
                    "humidity": 86,
                    "wind_speed": 0.99,
                    "pressure": 1011,
                    "description": "broken clouds"
                }
            }
        ],
        "follow_up_question": "Optional follow-up question for chat continuation"
    }
    
    Returns:
    {
        "success": true,
        "summary": "AI-generated summary...",
        "category": "Category name",
        "chat_session_id": "unique_id"
    }
    """
    try:
        # Validate request data
        request_serializer = GenerateReportRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response({
                "success": False,
                "error": "Invalid request data",
                "details": request_serializer.errors
            }, status=400)
        
        categories = request_serializer.validated_data.get('categories', [])
        follow_up_question = request.data.get('follow_up_question', None)
        previous_context = request.data.get('previous_context', None)
        
        # Initialize Gemini client with chat capability
        genai.configure(api_key=decouple.config("GEMINI_API_KEY", default=""))
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Process only the first category (single summary at a time)
        if not categories:
            return Response({
                "success": False,
                "error": "No categories provided"
            }, status=400)
            
        cat_data = categories[0]  # Take only first category
        category = cat_data.get('category')
        parameters = cat_data.get('parameters', [])
        values = cat_data.get('values', {})
        aqi = cat_data.get('aqi', 'N/A')
        location = cat_data.get('location', 'Unknown location')
        weather = cat_data.get('weather', {})
        
        if not category:
            return Response({
                "success": False,
                "error": "Category name is required"
            }, status=400)
        
        # Build context for AI including weather data
        pollutant_info = []
        for param in parameters:
            value = values.get(param, 'N/A')
            pollutant_info.append(f"{param}: {value} μg/m³")
        
        pollutant_text = ", ".join(pollutant_info) if pollutant_info else "No data available"
        
        # Build weather context
        weather_info = []
        if weather.get('temperature'):
            weather_info.append(f"Temperature: {weather.get('temperature')}°C")
        if weather.get('humidity'):
            weather_info.append(f"Humidity: {weather.get('humidity')}%")
        if weather.get('wind_speed'):
            weather_info.append(f"Wind Speed: {weather.get('wind_speed')} m/s")
        if weather.get('pressure'):
            weather_info.append(f"Pressure: {weather.get('pressure')} hPa")
        if weather.get('description'):
            weather_info.append(f"Conditions: {weather.get('description')}")
        
        weather_text = ", ".join(weather_info) if weather_info else "Weather data not available"
        
        # Handle follow-up questions (chat continuation)
        if follow_up_question and previous_context:
            prompt = f"""Previous context:
{previous_context}

User's follow-up question: {follow_up_question}

Provide a helpful, concise answer (2-3 sentences) based on the air quality and weather data."""
        else:
            # Create category-specific prompts with weather data
            prompts = {
                "Agriculture Consultation": f"""Based on the current environmental data for {location}:

Air Quality:
- AQI: {aqi}
- Pollutants: {pollutant_text}

Weather Conditions:
- {weather_text}

Provide a comprehensive 4-5 sentence summary for farmers including:
1. Impact of air quality AND weather on crop health and photosynthesis
2. How temperature, humidity, and wind affect pollutant dispersion
3. Recommended farming practices considering both air quality and weather
4. Best crops to plant in current conditions
Keep it practical and actionable.""",

                "Health Advisory": f"""Based on the current environmental data for {location}:

Air Quality:
- AQI: {aqi}
- Pollutants: {pollutant_text}

Weather Conditions:
- {weather_text}

Provide a comprehensive 4-5 sentence health advisory including:
1. Who is most at risk considering both air quality and weather
2. How temperature and humidity affect pollutant impacts on health
3. Recommended precautions and activities to avoid
4. Tips to reduce exposure in current weather conditions
Keep it clear and medically sound.""",

                "Air Quality Report": f"""Based on the current environmental data for {location}:

Air Quality:
- AQI: {aqi}
- Pollutants: {pollutant_text}

Weather Conditions:
- {weather_text}

Provide a comprehensive 4-5 sentence technical summary including:
1. Overall air quality assessment in context of weather conditions
2. Primary pollutants of concern and weather factors affecting them
3. How temperature, wind, and humidity influence air quality
4. Trend analysis and outlook considering weather patterns
Keep it scientific but accessible.""",

                "Emergency Services": f"""Based on the current environmental data for {location}:

Air Quality:
- AQI: {aqi}
- Pollutants: {pollutant_text}

Weather Conditions:
- {weather_text}

Provide a comprehensive 4-5 sentence emergency response summary including:
1. Severity level considering both air quality and weather conditions
2. How weather amplifies or reduces health risks
3. When to seek medical help
4. Emergency measures for vulnerable groups in current conditions
Keep it urgent and actionable."""
            }
            
            # Use default prompt if category not in predefined list
            prompt = prompts.get(category, f"""Based on the current environmental data for {location}:

Air Quality:
- AQI: {aqi}
- Pollutants: {pollutant_text}

Weather Conditions:
- {weather_text}

Provide a comprehensive 4-5 sentence summary for the category "{category}" with actionable insights considering both air quality and weather conditions.""")
        
        try:
            # Start or continue chat session
            if previous_context:
                # Continue existing chat
                chat = model.start_chat()
                response = chat.send_message(prompt)
            else:
                # New conversation
                response = model.generate_content(prompt)
            
            summary_text = response.text.strip()
            
            # Generate session ID for chat continuation
            import hashlib
            import time
            session_id = hashlib.md5(f"{category}{location}{time.time()}".encode()).hexdigest()
            
            response_data = {
                "success": True,
                "summary": summary_text,
                "category": category,
                "chat_session_id": session_id,
                "context": f"Category: {category}\nLocation: {location}\nAQI: {aqi}\nPollutants: {pollutant_text}\nWeather: {weather_text}\n\nSummary: {summary_text}"
            }
            
            return Response(response_data)
            
        except Exception as ai_error:
            return Response({
                "success": False,
                "error": f"Unable to generate summary: {str(ai_error)}"
            }, status=500)
        
    except Exception as e:
        return Response({
            "success": False,
            "error": f"Failed to generate report: {str(e)}"
        }, status=500)