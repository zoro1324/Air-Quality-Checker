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
    print(client)
    latest_data = client.locations.list(
        coordinates=(28.6139, 77.2090),
        radius=5000,
        limit=100
    )
    
    # Normalize first result for JSON safety
    results = getattr(latest_data, 'results', None)
    if results is None:
        results = latest_data if isinstance(latest_data, list) else []

    payload = []
    for loc in results:
        loc_id = getattr(loc, 'id', None)
        if loc_id is None and isinstance(loc, dict):
            loc_id = loc.get('id') or loc.get('locationId') or loc.get('location_id')

        name = getattr(loc, 'name', None) if not isinstance(loc, dict) else loc.get('name')
        city = (getattr(loc, 'city', None) or getattr(loc, 'city_name', None)) if not isinstance(loc, dict) else (loc.get('city') or loc.get('city_name'))
        country = (getattr(loc, 'country', None) or getattr(loc, 'country_code', None)) if not isinstance(loc, dict) else (loc.get('country') or loc.get('country_code'))

        coords = getattr(loc, 'coordinates', None) or getattr(loc, 'coord', None)
        if isinstance(loc, dict):
            coords = loc.get('coordinates') or loc.get('coord') or coords
        lat = lon = None
        if coords is not None:
            if isinstance(coords, dict):
                lat = coords.get('latitude') or coords.get('lat')
                lon = coords.get('longitude') or coords.get('lon')
            else:
                lat = getattr(coords, 'latitude', getattr(coords, 'lat', None))
                lon = getattr(coords, 'longitude', getattr(coords, 'lon', None))

        payload.append({
            'id': loc_id,
            'name': name,
            'city': city,
            'country': country,
            'latitude': lat,
            'longitude': lon,
        })

    print(payload[:1])
    return Response({
        "message": "Latest measurements fetched successfully.",
        "count": len(payload),
        "data": payload[:10],  # return a small sample
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
            bbox=(76.1667,7.9119,80.8167,13.6453),
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

            name = getattr(loc, 'name', None)
            if name is None and isinstance(loc, dict):
                name = loc.get('name')
            city = getattr(loc, 'city', None) or getattr(loc, 'city_name', None)
            if city is None and isinstance(loc, dict):
                city = loc.get('city') or loc.get('city_name')
            country = getattr(loc, 'country', None) or getattr(loc, 'country_code', None)
            if country is None and isinstance(loc, dict):
                country = loc.get('country') or loc.get('country_code')

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

            # Build geometry point if lat/lon available
            geom = None
            if latitude is not None and longitude is not None:
                try:
                    geom = Point(float(longitude), float(latitude), srid=4326)
                except Exception:
                    geom = None

            Location.objects.update_or_create(
                location_id=loc_id,
                defaults={
                    'latitude': latitude,
                    'longitude': longitude,
                    'geom': geom,
                }
            )
            inserted_count += 1

        page += 1

    return Response({"message": f"Inserted/Updated {inserted_count} locations successfully"})
