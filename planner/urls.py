from django.urls import path

from . import views

app_name = 'planner'

urlpatterns = [
    path('', views.PlanificacionListView.as_view(), name='list'),
    path('nueva/', views.PlanificacionCreateView.as_view(), name='create'),
    path('<int:pk>/', views.planificacion_detail, name='detail'),
    path('<int:pk>/editar/', views.PlanificacionUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.PlanificacionDeleteView.as_view(), name='delete'),
]
