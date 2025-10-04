from rest_framework.decorators import api_view
from rest_framework.response import Response
from openaq import OpenAQ
import decouple
from .models import Location, Measurement
from django.contrib.gis.geos import Point

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
