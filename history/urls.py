from django.urls import path
from . import views

app_name = 'history'

urlpatterns = [
    path('', views.HistorialListView.as_view(), name='list'),
    path('<int:pk>/', views.HistorialDetailView.as_view(), name='detail'),
    path('generar/', views.generar_historial_hoy, name='generar'),
]
