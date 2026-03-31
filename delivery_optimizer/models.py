from django.db import models
from clients.models import Cliente
from django.contrib.auth import get_user_model

class DeliveryConfig(models.Model):
    DAYS_OF_WEEK = [
        ("mon", "Lunes"),
        ("tue", "Martes"),
        ("wed", "Miércoles"),
        ("thu", "Jueves"),
        ("fri", "Viernes"),
        ("sat", "Sábado"),
        ("sun", "Domingo"),
    ]
    days_of_week = models.JSONField()
    clients = models.ManyToManyField(Cliente)
    num_vehicles = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)

class OptimizationResult(models.Model):
    STRATEGY_CHOICES = [
        ("light", "Leve optimización"),
        ("medium", "Media optimización"),
        ("high", "Alta optimización"),
    ]
    delivery_config = models.ForeignKey(DeliveryConfig, on_delete=models.CASCADE)
    strategy = models.CharField(max_length=10, choices=STRATEGY_CHOICES)
    assignments = models.JSONField()
    explanation = models.TextField()
    vehicles_needed = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
