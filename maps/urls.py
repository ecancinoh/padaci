from django.urls import path
from . import views

app_name = 'maps'

urlpatterns = [
    path('', views.mapa_chile, name='mapa'),
    path('geojson/', views.clientes_geojson, name='geojson'),
]
