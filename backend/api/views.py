from rest_framework.decorators import api_view
from rest_framework.response import Response
from openaq import OpenAQ
import decouple
from .models import Location, Measurement
from django.contrib.gis.geos import Point
import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError

# Create your views here.

@api_view(['GET'])
def latest_measurements(request):
    OPENAQ_API = decouple.config("OPENAQ_API")
    client = OpenAQ(OPENAQ_API)

    # Optional: override location via query param
    loc_id_param = request.query_params.get('locations_id') or request.query_params.get('location_id')
    try:
        locations_id = int(loc_id_param) if loc_id_param is not None else 3409527
    except (TypeError, ValueError):
        return Response({"error": "locations_id must be an integer"}, status=400)

    latest_data = client.locations.latest(locations_id=locations_id)

    def get_attr(obj, name, default=None):
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def to_int(v):
        try:
            return None if v is None else int(v)
        except Exception:
            return None

    def to_float(v):
        try:
            return None if v is None else float(v)
        except Exception:
            return None

    results_raw = getattr(latest_data, 'results', None)
    if results_raw is None:
        results_raw = latest_data if isinstance(latest_data, list) else []

    serialized = []
    for item in results_raw:
        sensors_id = to_int(get_attr(item, 'sensors_id'))

        # Map sensors_id -> pollutant using if/elif conditions
        pollutant = None
        if sensors_id == 12238696:
            pollutant = 'CO'
        elif sensors_id == 12238697:
            pollutant = 'SO₂'
        elif sensors_id == 12238698:
            pollutant = 'NO₂'
        elif sensors_id == 12238699:
            pollutant = 'PM10'
        elif sensors_id == 12238700:
            pollutant = 'PM2.5'
        elif sensors_id == 12238701:
            pollutant = 'O₃'
        elif sensors_id == 12238702:
            pollutant = 'NH₃'
        elif sensors_id == 12238703:
            pollutant = 'NO'
        elif sensors_id == 12238704:
            pollutant = 'NOx'

        dt = get_attr(item, 'datetime')
        coords = get_attr(item, 'coordinates')
        lat = get_attr(coords, 'latitude') if coords is not None else None
        lon = get_attr(coords, 'longitude') if coords is not None else None

        serialized.append({
            'sensors_id': sensors_id,
            'pollutant': pollutant,
            'value': to_float(get_attr(item, 'value')),
            'datetime_utc': get_attr(dt, 'utc') if dt is not None else None,
            'datetime_local': get_attr(dt, 'local') if dt is not None else None,
            'latitude': to_float(lat),
            'longitude': to_float(lon),
            'locations_id': to_int(get_attr(item, 'locations_id')),
        })

    return Response({
        "message": "Latest measurements with pollutant mapping.",
        "count": len(serialized),
        "results": serialized,
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
