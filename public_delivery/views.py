from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.mixins import admin_supervisor_required
from .models import EntregaPublica, EventoParada, ParadaPublica


# ── Public: Tracking API ──────────────────────────────────────────────────────

def tracking_api(request):
    code = request.GET.get('codigo', '').strip().upper()
    if not code:
        return JsonResponse({'error': 'Código requerido'}, status=400)

    try:
        entrega = (
            EntregaPublica.objects
            .prefetch_related('paradas')
            .get(tracking_code=code)
        )
    except EntregaPublica.DoesNotExist:
        return JsonResponse({'error': 'No encontrada'}, status=404)

    return JsonResponse({
        'id': entrega.pk,
        'tracking_code': entrega.tracking_code,
        'vehicle': entrega.vehicle,
        'status': entrega.status,
        'driver_name': entrega.driver_name or None,
        'scheduled_for': entrega.scheduled_for.isoformat() if entrega.scheduled_for else None,
        'paradas': [
            {
                'id': p.pk,
                'stop_order': p.stop_order,
                'label': p.label,
                'address': p.address,
                'status': p.status,
                'delivered_at': p.delivered_at.isoformat() if p.delivered_at else None,
            }
            for p in entrega.paradas.all()
        ],
    })


# ── Conductor panel ───────────────────────────────────────────────────────────

@login_required
def conductor_panel(request):
    if not hasattr(request.user, 'rol') or request.user.rol not in ('conductor', 'admin'):
        messages.error(request, 'Solo conductores pueden acceder a esta sección.')
        return redirect('accounts:login')

    entregas = (
        EntregaPublica.objects
        .filter(
            driver=request.user,
            status__in=[
                EntregaPublica.STATUS_SCHEDULED,
                EntregaPublica.STATUS_PICKED_UP,
                EntregaPublica.STATUS_IN_ROUTE,
            ]
        )
        .prefetch_related('paradas')
        .order_by('scheduled_for')
    )

    return render(request, 'public_delivery/conductor/panel.html', {
        'entregas': entregas,
    })


@login_required
@require_POST
def conductor_actualizar_estado(request):
    if not hasattr(request.user, 'rol') or request.user.rol not in ('conductor', 'admin'):
        return JsonResponse({'error': 'Sin permiso'}, status=403)

    tipo = request.POST.get('tipo')  # 'ruta' o 'parada'
    entrega_id = request.POST.get('entrega_id')
    nuevo_estado = request.POST.get('estado')

    ESTADOS_VALIDOS = [s[0] for s in EntregaPublica.STATUS_CHOICES]
    if nuevo_estado not in ESTADOS_VALIDOS:
        return JsonResponse({'error': 'Estado inválido'}, status=400)

    try:
        entrega = EntregaPublica.objects.get(pk=entrega_id, driver=request.user)
    except EntregaPublica.DoesNotExist:
        return JsonResponse({'error': 'Entrega no encontrada'}, status=404)

    if tipo == 'ruta':
        entrega.status = nuevo_estado
        entrega.save(update_fields=['status', 'updated_at'])
        EventoParada.objects.create(
            entrega=entrega,
            note=f'Estado de ruta actualizado a: {entrega.get_status_display()}',
            created_by=request.user,
        )
        return JsonResponse({'ok': True, 'nuevo_estado': nuevo_estado})

    if tipo == 'parada':
        parada_id = request.POST.get('parada_id')
        try:
            parada = ParadaPublica.objects.get(pk=parada_id, entrega=entrega)
        except ParadaPublica.DoesNotExist:
            return JsonResponse({'error': 'Parada no encontrada'}, status=404)

        parada.status = nuevo_estado
        if nuevo_estado == EntregaPublica.STATUS_DELIVERED:
            parada.delivered_at = timezone.now()
        parada.save(update_fields=['status', 'delivered_at'])

        EventoParada.objects.create(
            entrega=entrega,
            parada=parada,
            note=f'{parada.label}: {parada.get_status_display()}',
            created_by=request.user,
        )

        # Auto-avanzar estado de la ruta
        todas = list(entrega.paradas.values_list('status', flat=True))
        if all(s == EntregaPublica.STATUS_DELIVERED for s in todas):
            entrega.status = EntregaPublica.STATUS_DELIVERED
            entrega.save(update_fields=['status', 'updated_at'])
        elif any(s in (EntregaPublica.STATUS_IN_ROUTE, EntregaPublica.STATUS_DELIVERED) for s in todas):
            if entrega.status == EntregaPublica.STATUS_PICKED_UP:
                entrega.status = EntregaPublica.STATUS_IN_ROUTE
                entrega.save(update_fields=['status', 'updated_at'])

        return JsonResponse({
            'ok': True,
            'nuevo_estado': nuevo_estado,
            'delivered_at': parada.delivered_at.isoformat() if parada.delivered_at else None,
            'ruta_status': entrega.status,
        })

    return JsonResponse({'error': 'tipo inválido'}, status=400)


# ── Portal admin (admin/supervisor) ──────────────────────────────────────────

@admin_supervisor_required
def portal_entregas_list(request):
    qs = (
        EntregaPublica.objects
        .select_related('driver')
        .prefetch_related('paradas')
        .order_by('-created_at')
    )
    estado_filter = request.GET.get('estado', '')
    if estado_filter:
        qs = qs.filter(status=estado_filter)

    return render(request, 'public_delivery/portal/list.html', {
        'entregas': qs,
        'estado_filter': estado_filter,
        'status_choices': EntregaPublica.STATUS_CHOICES,
    })


@admin_supervisor_required
def portal_entrega_create(request):
    from accounts.models import CustomUser

    conductores = CustomUser.objects.filter(rol='conductor', activo=True).order_by('last_name', 'first_name')

    if request.method == 'POST':
        vehicle = request.POST.get('vehicle', EntregaPublica.VEHICLE_JAC)
        driver_id = request.POST.get('driver') or None
        scheduled_for = request.POST.get('scheduled_for') or None
        client_name = request.POST.get('client_name', '').strip()
        client_phone = request.POST.get('client_phone', '').strip()
        notes = request.POST.get('notes', '').strip()

        entrega = EntregaPublica.objects.create(
            vehicle=vehicle,
            driver_id=driver_id,
            scheduled_for=scheduled_for,
            client_name=client_name,
            client_phone=client_phone,
            notes=notes,
        )

        # Paradas
        paradas_labels = request.POST.getlist('parada_label')
        paradas_address = request.POST.getlist('parada_address')
        for i, (label, address) in enumerate(zip(paradas_labels, paradas_address), start=1):
            label = label.strip()
            address = address.strip()
            if label:
                ParadaPublica.objects.create(
                    entrega=entrega,
                    stop_order=i,
                    label=label,
                    address=address,
                )

        messages.success(request, f'Entrega {entrega.tracking_code} creada correctamente.')
        return redirect('public_delivery:portal_list')

    return render(request, 'public_delivery/portal/form.html', {
        'conductores': conductores,
        'vehicle_choices': EntregaPublica.VEHICLE_CHOICES,
        'titulo': 'Nueva entrega pública',
    })


@admin_supervisor_required
def portal_entrega_detail(request, pk):
    entrega = get_object_or_404(
        EntregaPublica.objects.select_related('driver').prefetch_related('paradas', 'eventos__created_by'),
        pk=pk,
    )
    return render(request, 'public_delivery/portal/detail.html', {
        'entrega': entrega,
        'status_choices': EntregaPublica.STATUS_CHOICES,
    })


@admin_supervisor_required
@require_POST
def portal_entrega_edit_status(request, pk):
    entrega = get_object_or_404(EntregaPublica, pk=pk)
    nuevo = request.POST.get('status')
    if nuevo in [s[0] for s in EntregaPublica.STATUS_CHOICES]:
        entrega.status = nuevo
        entrega.save(update_fields=['status', 'updated_at'])
        EventoParada.objects.create(
            entrega=entrega,
            note=f'Estado actualizado manualmente a: {entrega.get_status_display()}',
            created_by=request.user,
        )
        messages.success(request, 'Estado actualizado.')
    return redirect('public_delivery:portal_detail', pk=pk)
