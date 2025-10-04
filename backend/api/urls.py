
from django.urls import path

from . import views

urlpatterns = [
    path('aqi/latest/', views.latest_measurements, name='latest_measurements'),
]

# myapp.urls +/+ api.urls