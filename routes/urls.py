from django.urls import path
from . import views

app_name = 'routes'

urlpatterns = [
    path('', views.RutaListView.as_view(), name='list'),
    path('falabella/nueva/', views.ruta_falabella_import, name='falabella_import'),
    path('falabella/<int:pk>/', views.ruta_falabella_detail, name='falabella_detail'),
    path('falabella/<int:pk>/reoptimizar/', views.falabella_reoptimizar, name='falabella_reoptimizar'),
    path('falabella/<int:pk>/reordenar/', views.falabella_reordenar_paradas, name='falabella_reordenar'),
    path('falabella/<int:pk>/parada/<int:parada_id>/entregado/', views.falabella_marcar_entregado, name='falabella_marcar_entregado'),
    path('falabella/<int:pk>/parada/<int:parada_id>/candidato/<int:candidato_id>/seleccionar/', views.falabella_seleccionar_candidato, name='falabella_select_candidate'),
    path('falabella/<int:pk>/parada/<int:parada_id>/direccion/', views.falabella_actualizar_direccion, name='falabella_update_address'),
    path('entregas/', views.EntregaRutaListView.as_view(), name='entregas_list'),
    path('entregas/nueva/', views.EntregaRutaCreateView.as_view(), name='entregas_create'),
    path('entregas/<int:pk>/', views.EntregaRutaDetailView.as_view(), name='entregas_detail'),
    path('entregas/<int:pk>/editar/', views.EntregaRutaUpdateView.as_view(), name='entregas_update'),
    path('entregas/<int:pk>/eliminar/', views.EntregaRutaDeleteView.as_view(), name='entregas_delete'),
    path('entregas/<int:pk>/estado/', views.entrega_actualizar_estado, name='entregas_update_estado'),
    path('entregas/<int:pk>/pagos/<int:pago_pk>/eliminar/', views.eliminar_pago_entrega, name='entregas_delete_pago'),
    path('entregas/eliminar-masiva/', views.entregas_eliminar_masiva, name='entregas_eliminar_masiva'),
    path('nueva/', views.RutaCreateView.as_view(), name='create'),
    path('<int:pk>/', views.RutaDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.RutaUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.RutaDeleteView.as_view(), name='delete'),
    path('<int:pk>/procesar-foto/', views.procesar_foto_ruta, name='procesar_foto'),
    path('<int:pk>/crear-cliente-rapido/', views.crear_cliente_rapido_desde_ruta, name='crear_cliente_rapido'),
    path('<int:pk>/crear-entregas/', views.crear_entregas_desde_ruta, name='crear_entregas'),
    path('<int:pk>/optimizar/', views.optimizar_ruta, name='optimizar'),
    path('<int:pk>/buscar-por-texto/', views.buscar_por_texto_ruta, name='buscar_por_texto'),
    path('<int:pk>/navegacion/', views.navegacion_ruta, name='navegacion'),
    path('<int:pk>/reoptimizar-posicion/', views.reoptimizar_desde_posicion, name='reoptimizar_posicion'),
    path('<int:pk>/actualizar-parada/', views.actualizar_estado_parada, name='actualizar_parada'),
    path('<int:pk>/eliminar-parada/', views.eliminar_parada_ruta, name='eliminar_parada'),
    path('buscar-clientes/', views.buscar_clientes, name='buscar_clientes'),
]
