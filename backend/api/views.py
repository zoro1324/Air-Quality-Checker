from ast import Await
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

from openepi_client import GeoLocation, BoundingBox
from openepi_client.soil import SoilClient
from openepi_client.soil import AsyncSoilClient

# sync

# Get the mean and the 0.05 quantile of the soil 
# properties at the queried location and depths       
def soil_properties_view(request):
    properties = ["clay", "silt"]
    depths = ["0-5cm", "5-15cm"]
    values = ["mean", "Q0.05"]
    soil_property = SoilClient.get_soil_property(geolocation=GeoLocation(lat=60.1, lon=9.58), depths=depths, properties=properties, values=values)

# async

# Get the mean and the 0.05 quantile of the soil 
# properties at the queried location and depths       
def async_soil_properties_view(request):
    properties = ["clay", "silt"]
    depths = ["0-5cm", "5-15cm"]
    values = ["mean", "Q0.05"]
    soil_property = Await(AsyncSoilClient.get_soil_property(geolocation=GeoLocation(lat=60.1, lon=9.58), depths=depths, properties=properties,values=values))