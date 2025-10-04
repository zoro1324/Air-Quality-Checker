
from django.contrib.gis.db import models

class Location(models.Model):
    location_id = models.IntegerField(primary_key=True)  # ISO country code
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    geom = models.PointField(srid=4326, blank=True, null=True)
    # Geometry point in WGS84 (SRID 4326). Nullable to allow backfill from existing lat/lon.

    def __str__(self):
        return f"{self.name} ({self.city}, {self.country})"

    class Meta:
        pass

class Measurement(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='measurements')
    parameter = models.CharField(max_length=50, blank=True, null=True)
    value = models.FloatField(blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.parameter} = {self.value} {self.unit} at {self.last_updated}"

    class Meta:
        indexes = [
            # Add an index to speed up lookups by location foreign key
            models.Index(fields=["location"]),
        ]
