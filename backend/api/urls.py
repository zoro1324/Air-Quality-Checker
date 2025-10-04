
from django.urls import path

from . import views

urlpatterns = [
    path('aqi/latest/', views.latest_measurements, name='latest_measurements'),
    path('aqi/insert/', views.instert_data, name='insert_data'),
]

# myapp.urls +/+ api.urls