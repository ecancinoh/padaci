from django.urls import path
from . import views

app_name = 'deliveries'

urlpatterns = [
    path('', views.EntregaListView.as_view(), name='list'),
    path('nueva/', views.EntregaCreateView.as_view(), name='create'),
    path('<int:pk>/', views.EntregaDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.EntregaUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.EntregaDeleteView.as_view(), name='delete'),
    path('<int:pk>/estado/', views.actualizar_estado, name='update_estado'),
]
