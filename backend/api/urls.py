
from django.urls import path

from . import views

urlpatterns = [
    path('aqi/latest/', views.latest_measurements, name='latest_measurements'),
    path('aqi/insert/', views.instert_data, name='insert_data'),
    path('weather/latest/', views.latest_weather, name='latest_weather'),
    path('aqi/predict/', views.predict_aqi, name='predict_aqi'),
    path('generate-report/', views.generate_report, name='generate_report'),
    path('prediction-followup/', views.prediction_followup, name='prediction_followup'),
]

# myapp.urls +/+ api.urls