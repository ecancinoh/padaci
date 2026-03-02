"""
PADACI – URL Configuration principal
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),

    # Raíz → redirige al dashboard
    path('', lambda request: redirect('dashboard:index'), name='home'),

    # Módulos del sistema
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('clientes/', include('clients.urls', namespace='clients')),
    path('empresas/', include('companies.urls', namespace='companies')),
    path('entregas/', include('deliveries.urls', namespace='deliveries')),
    path('historial/', include('history.urls', namespace='history')),
    path('mapa/', include('maps.urls', namespace='maps')),
    path('rutas/', include('routes.urls', namespace='routes')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

