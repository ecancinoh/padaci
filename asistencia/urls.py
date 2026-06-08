from django.urls import path

from . import views

app_name = 'asistencia'


urlpatterns = [
    path('', views.AsistenciaListView.as_view(), name='list'),
    path('diaria/', views.asistencia_diaria, name='diaria'),
    path('individual/', views.AsistenciaIndividualView.as_view(), name='individual'),
    path('<int:pk>/editar/', views.AsistenciaUpdateView.as_view(), name='update'),
    path('reporte-mensual/', views.AsistenciaReporteMensualView.as_view(), name='reporte_mensual'),
]
