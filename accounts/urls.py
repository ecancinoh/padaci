from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.UsuarioListView.as_view(), name='list'),
    path('nuevo/', views.UsuarioCreateView.as_view(), name='create'),
    path('<int:pk>/', views.UsuarioDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.UsuarioDeleteView.as_view(), name='delete'),
]
