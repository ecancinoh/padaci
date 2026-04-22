from django.urls import path
from . import views

app_name = 'rendiciones'

urlpatterns = [
    path('', views.RendicionListView.as_view(), name='list'),
    path('plantilla-excel/', views.plantilla_excel, name='plantilla_excel'),
    path('resumen-excel/', views.rendiciones_resumen_excel, name='resumen_excel'),
    path('nueva/', views.rendicion_create, name='create'),
    path('<int:pk>/', views.RendicionDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.rendicion_update, name='update'),
    path('<int:pk>/excel/', views.rendicion_excel, name='excel'),
    path('<int:pk>/pdf/', views.rendicion_pdf, name='pdf'),
    path('<int:pk>/eliminar/', views.RendicionDeleteView.as_view(), name='delete'),
]
