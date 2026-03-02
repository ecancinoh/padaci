from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from clients.models import Cliente


@login_required
def mapa_chile(request):
    """Vista principal del mapa de Chile con marcadores de clientes."""
    clientes = Cliente.objects.filter(activo=True, latitud__isnull=False, longitud__isnull=False)
    return render(request, 'maps/mapa.html', {'clientes': clientes})


@login_required
def clientes_geojson(request):
    """Endpoint JSON con los clientes geolocalizados para Leaflet."""
    clientes = Cliente.objects.filter(activo=True, latitud__isnull=False, longitud__isnull=False)
    features = []
    for c in clientes:
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [float(c.longitud), float(c.latitud)],
            },
            'properties': {
                'id': c.pk,
                'nombre': str(c),
                'direccion': c.direccion,
                'ciudad': c.ciudad,
                'telefono': c.telefono or '',
                'empresa': str(c.empresa) if c.empresa else '',
            },
        })
    return JsonResponse({'type': 'FeatureCollection', 'features': features})
