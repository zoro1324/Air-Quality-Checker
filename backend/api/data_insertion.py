import decouple
from openaq import OpenAQ
from .models import Location
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings') 
django.setup()
OPENAQ_API = decouple.config("OPENAQ_API")
client = OpenAQ(OPENAQ_API)
page = 1
limit = 100
inserted_count = 0

while True:
    response = client.locations.list(page=page, limit=limit)
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
        Location.objects.update_or_create(
            location_id=loc_id,
            defaults={
                'name': name,
                'city': city,
                'country': country,
                'latitude': latitude,
                'longitude': longitude,
            }
        )
        inserted_count += 1
    page += 1

print("Sucessful..........")