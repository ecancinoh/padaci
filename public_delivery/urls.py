from django.urls import path
from . import views

app_name = 'public_delivery'

urlpatterns = [
    # Public tracking API
    path('seguimiento/api/', views.tracking_api, name='tracking_api'),

    # Conductor panel
    path('app/conductor/', views.conductor_panel, name='conductor_panel'),
    path('app/conductor/api/estado/', views.conductor_actualizar_estado, name='conductor_actualizar_estado'),

    # Portal admin
    path('entregas-publicas/', views.portal_entregas_list, name='portal_list'),
    path('entregas-publicas/nueva/', views.portal_entrega_create, name='portal_create'),
    path('entregas-publicas/<int:pk>/', views.portal_entrega_detail, name='portal_detail'),
    path('entregas-publicas/<int:pk>/estado/', views.portal_entrega_edit_status, name='portal_edit_status'),
]
