from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('', views.EmpresaListView.as_view(), name='list'),
    path('nueva/', views.EmpresaCreateView.as_view(), name='create'),
    path('<int:pk>/', views.EmpresaDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.EmpresaUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.EmpresaDeleteView.as_view(), name='delete'),
]
