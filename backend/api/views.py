from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from openaq import OpenAQ
import decouple
# Create your views here.

@api_view(['GET'])
def latest_measurements(request):
    OPENAQ_API = decouple.config("OPENAQ_API")
    client = OpenAQ(api_key='1e8d7cdfee4a3c725868b9148839b5323da06cb794cac768098de81167289e3d')
    print(client)
    latest_data = client.locations.list(
        coordinates=(28.6139, 77.2090),
        radius=5000,
        limit=100
    )
    
    print(latest_data)
    return Response({
        "message": "Latest measurements fetched successfully.",
        "data": latest_data[0]
    })
    
