from django.urls import path
from . import views

app_name = "delivery_optimizer"

urlpatterns = [
    path("config/", views.delivery_config_create, name="delivery_config_create"),
    path("results/<int:config_id>/", views.optimization_results, name="optimization_results"),
]
