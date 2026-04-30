from django.urls import path

from . import views


app_name = 'informe_servicio'


urlpatterns = [
    path('', views.InformeServicioView.as_view(), name='index'),
    path('excel/', views.exportar_excel, name='excel'),
    path('pdf/', views.exportar_pdf, name='pdf'),
]
