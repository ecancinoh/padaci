
import os
from django.urls import path
from . import views

# Log when dashboard.urls is loaded
try:
    with open('/tmp/dashboard_urls_loaded.log', 'a', encoding='utf-8') as f:
        f.write('dashboard/urls.py loaded\n')
except Exception:
    pass

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
]
