from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from .forms import DeliveryConfigForm
from .models import DeliveryConfig, OptimizationResult
from django.conf import settings
import os

@staff_member_required
def delivery_config_create(request):
    if request.method == "POST":
        form = DeliveryConfigForm(request.POST)
        if form.is_valid():
            config = form.save(commit=False)
            config.created_by = request.user
            config.save()
            form.save_m2m()

            # Llamar a Gemini para cada estrategia y guardar resultados
            from .services import call_gemini_api
            strategies = [
                ("light", "Leve optimización"),
                ("medium", "Media optimización"),
                ("high", "Alta optimización"),
            ]
            clients = config.clients.all()
            for strategy, _ in strategies:
                try:
                    gemini_result = call_gemini_api(clients, config.num_vehicles, config.days_of_week, strategy=strategy)
                    OptimizationResult.objects.create(
                        delivery_config=config,
                        strategy=strategy,
                        assignments=gemini_result.get("assignments", {}),
                        explanation=gemini_result.get("explanation", f"Resultado simulado para {strategy}"),
                        vehicles_needed=gemini_result.get("vehicles_needed", config.num_vehicles),
                    )
                except Exception as e:
                    OptimizationResult.objects.create(
                        delivery_config=config,
                        strategy=strategy,
                        assignments={},
                        explanation=f"Error al consultar Gemini: {e}",
                        vehicles_needed=config.num_vehicles,
                    )
            return redirect("delivery_optimizer:optimization_results", config_id=config.id)
    else:
        form = DeliveryConfigForm()
    return render(request, "delivery_optimizer/delivery_config_form.html", {"form": form})

@staff_member_required
def optimization_results(request, config_id):
    config = DeliveryConfig.objects.get(id=config_id)
    results = OptimizationResult.objects.filter(delivery_config=config)
    return render(request, "delivery_optimizer/optimization_results.html", {"config": config, "results": results})
