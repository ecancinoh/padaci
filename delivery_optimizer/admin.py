from django.contrib import admin
from .models import DeliveryConfig, OptimizationResult

@admin.register(DeliveryConfig)
class DeliveryConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "created_by", "created_at", "num_vehicles")
    filter_horizontal = ("clients",)

@admin.register(OptimizationResult)
class OptimizationResultAdmin(admin.ModelAdmin):
    list_display = ("id", "delivery_config", "strategy", "vehicles_needed", "created_at")
