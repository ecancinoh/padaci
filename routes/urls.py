from django.urls import path
from . import views

app_name = 'routes'

urlpatterns = [
    path('', views.RutaListView.as_view(), name='list'),
    path('nueva/', views.RutaCreateView.as_view(), name='create'),
    path('<int:pk>/', views.RutaDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.RutaUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.RutaDeleteView.as_view(), name='delete'),
    path('<int:pk>/procesar-foto/', views.procesar_foto_ruta, name='procesar_foto'),
    path('<int:pk>/crear-entregas/', views.crear_entregas_desde_ruta, name='crear_entregas'),
    path('<int:pk>/optimizar/', views.optimizar_ruta, name='optimizar'),
    path('<int:pk>/buscar-por-texto/', views.buscar_por_texto_ruta, name='buscar_por_texto'),
    path('<int:pk>/navegacion/', views.navegacion_ruta, name='navegacion'),
    path('<int:pk>/reoptimizar-posicion/', views.reoptimizar_desde_posicion, name='reoptimizar_posicion'),
    path('<int:pk>/actualizar-parada/', views.actualizar_estado_parada, name='actualizar_parada'),
    path('buscar-clientes/', views.buscar_clientes, name='buscar_clientes'),
]
