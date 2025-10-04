import requests
from django.http import JsonResponse
from django.conf import settings

def get_weather(request, city):
    api_key = "YOUR_OPENWEATHER_API_KEY"  # store in .env for security
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    response = requests.get(url)
    data = response.json()

    return JsonResponse(data)

