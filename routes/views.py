import json
import math
import uuid
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from .models import RutaDia, ParadaRuta, Entrega
from .forms import RutaDiaForm, EntregaForm, EntregaEstadoForm
from clients.models import Cliente


class EntregaRutaListView(LoginRequiredMixin, ListView):
    model = Entrega
    template_name = 'deliveries/list.html'
    context_object_name = 'entregas'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('cliente', 'empresa', 'conductor')
        estado = self.request.GET.get('estado', '')
        fecha = self.request.GET.get('fecha', '')
        q = self.request.GET.get('q', '')
        if estado:
            qs = qs.filter(estado=estado)
        if fecha:
            qs = qs.filter(fecha_programada=fecha)
        if q:
            qs = qs.filter(numero_guia__icontains=q) | qs.filter(cliente__nombre__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['estados'] = Entrega.ESTADO_CHOICES
        return ctx


class EntregaRutaCreateView(LoginRequiredMixin, CreateView):
    model = Entrega
    form_class = EntregaForm
    template_name = 'deliveries/form.html'
    success_url = reverse_lazy('routes:entregas_list')

    def form_valid(self, form):
        messages.success(self.request, 'Entrega registrada exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Registrar Entrega'
        return ctx


class EntregaRutaUpdateView(LoginRequiredMixin, UpdateView):
    model = Entrega
    form_class = EntregaForm
    template_name = 'deliveries/form.html'
    success_url = reverse_lazy('routes:entregas_list')

    def form_valid(self, form):
        messages.success(self.request, 'Entrega actualizada correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Entrega'
        return ctx


class EntregaRutaDeleteView(LoginRequiredMixin, DeleteView):
    model = Entrega
    template_name = 'deliveries/confirm_delete.html'
    success_url = reverse_lazy('routes:entregas_list')

    def form_valid(self, form):
        messages.success(self.request, 'Entrega eliminada.')
        return super().form_valid(form)


class EntregaRutaDetailView(LoginRequiredMixin, DetailView):
    model = Entrega
    template_name = 'deliveries/detail.html'
    context_object_name = 'entrega'


@login_required
def entregas_eliminar_masiva(request):
    if request.method != 'POST':
        return redirect('routes:entregas_list')
    ids = request.POST.getlist('ids')
    if ids:
        qs = Entrega.objects.filter(pk__in=ids)
        total = qs.count()
        qs.delete()
        messages.success(request, f'{total} entrega(s) eliminada(s) correctamente.')
    else:
        messages.warning(request, 'No se seleccionó ninguna entrega.')
    return redirect('routes:entregas_list')


@login_required
def entrega_actualizar_estado(request, pk):
    entrega = get_object_or_404(Entrega, pk=pk)
    if request.method == 'POST':
        form = EntregaEstadoForm(request.POST, request.FILES, instance=entrega)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.estado == 'entregado' and not obj.fecha_entrega:
                obj.fecha_entrega = timezone.now()
            obj.save()
            messages.success(request, 'Estado actualizado correctamente.')
            return redirect('routes:entregas_detail', pk=pk)
    else:
        form = EntregaEstadoForm(instance=entrega)
    return render(request, 'deliveries/actualizar_estado.html', {'form': form, 'entrega': entrega})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _haversine(lat1, lon1, lat2, lon2):
    """Distancia en km entre dos coordenadas geográficas."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _nearest_neighbor_route(points):
    """
    Algoritmo Nearest Neighbor para TSP (Traveling Salesman Problem).
    Recibe lista de dicts con keys: id, lat, lon.
    Retorna lista ordenada de ids.
    """
    if not points:
        return []
    unvisited = list(points)
    # Punto de inicio: el primero (bodega o inicio del conductor)
    current = unvisited.pop(0)
    route = [current]
    while unvisited:
        nearest = min(unvisited, key=lambda p: _haversine(
            float(current['lat']), float(current['lon']),
            float(p['lat']), float(p['lon']),
        ))
        unvisited.remove(nearest)
        route.append(nearest)
        current = nearest
    return [p['id'] for p in route]


def _ocr_extract_names(image_path):
    """
    Extrae nombres de clientes de una imagen usando Google Gemini (gratis).
    Le pide directamente a la IA que liste los nombres que ve en la imagen.
    Retorna lista de líneas con los nombres detectados.
    """
    try:
        from google import genai
        from google.genai import types
        import PIL.Image
        from django.conf import settings

        api_key = settings.GEMINI_API_KEY
        if not api_key or api_key == 'TU_API_KEY_AQUI':
            return ['Error: Configura GEMINI_API_KEY en el archivo .env']

        client = genai.Client(api_key=api_key)
        img = PIL.Image.open(image_path)

        prompt = (
            "Esta imagen contiene una lista de clientes o destinatarios de un servicio de reparto. "
            "Lee todos los nombres de personas o empresas que aparecen en la imagen. "
            "Devuelve SOLO los nombres, uno por línea, sin numeración, sin guiones, sin texto adicional. "
            "Si hay texto que no sea un nombre (fechas, direcciones, números de teléfono), ignóralo."
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, img],
        )
        text = response.text.strip()
        lineas = [l.strip() for l in text.splitlines() if l.strip()]
        return lineas

    except Exception as e:
        msg = str(e)
        if '429' in msg or 'RESOURCE_EXHAUSTED' in msg:
            import re
            delay = re.search(r'retry in (\d+)', msg)
            segundos = delay.group(1) if delay else '60'
            return [f'Error: Cuota de Gemini agotada. Espera {segundos} segundos e intenta nuevamente.']
        return [f'Gemini Error: {msg}']


def _normalizar(texto):
    """Normaliza texto: minúsculas, sin tildes, sin puntuación extra."""
    import unicodedata
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto


def _match_clients_from_text(text_lines, umbral=0.52):
    """
    Para cada línea OCR busca el cliente cuyo nombre sea más similar
    usando difflib.SequenceMatcher.
    Solo acepta coincidencias con ratio >= umbral.
    Retorna tupla (clientes_encontrados, lineas_no_encontradas):
      - clientes_encontrados: lista de Clientes encontrados (sin duplicados)
      - lineas_no_encontradas: lista de strings de líneas que no tuvieron match
    """
    from difflib import SequenceMatcher

    # Cargar todos los clientes una sola vez
    todos = list(Cliente.objects.values('id', 'nombre'))
    nombres_norm = [(c['id'], _normalizar(c['nombre'])) for c in todos]

    found = []
    no_encontradas = []
    seen_ids = set()

    for linea in text_lines:
        linea_norm = _normalizar(linea)
        # Ignorar líneas muy cortas o que parezcan números/códigos
        if len(linea_norm) < 5:
            continue

        mejor_ratio = 0.0
        mejor_id = None

        for cid, nombre_norm in nombres_norm:
            ratio = SequenceMatcher(None, linea_norm, nombre_norm).ratio()
            if ratio > mejor_ratio:
                mejor_ratio = ratio
                mejor_id = cid

        if mejor_ratio >= umbral and mejor_id not in seen_ids:
            try:
                cliente = Cliente.objects.get(pk=mejor_id)
                found.append(cliente)
                seen_ids.add(mejor_id)
            except Cliente.DoesNotExist:
                no_encontradas.append(linea.strip())
        else:
            # No se encontró coincidencia suficiente → línea sin registrar
            if mejor_ratio < umbral:
                no_encontradas.append(linea.strip())

    return found, no_encontradas


# ── Views ──────────────────────────────────────────────────────────────────────

class RutaListView(LoginRequiredMixin, ListView):
    model = RutaDia
    template_name = 'routes/list.html'
    context_object_name = 'rutas'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('conductor', 'peoneta')
        fecha = self.request.GET.get('fecha', '')
        conductor = self.request.GET.get('conductor', '')
        if fecha:
            qs = qs.filter(fecha=fecha)
        if conductor:
            qs = qs.filter(conductor_id=conductor)
        return qs


class RutaCreateView(LoginRequiredMixin, CreateView):
    model = RutaDia
    form_class = RutaDiaForm
    template_name = 'routes/form.html'
    success_url = reverse_lazy('routes:list')

    def form_valid(self, form):
        messages.success(self.request, 'Ruta del día creada exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva Ruta del Día'
        return ctx


class RutaUpdateView(LoginRequiredMixin, UpdateView):
    model = RutaDia
    form_class = RutaDiaForm
    template_name = 'routes/form.html'
    success_url = reverse_lazy('routes:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Ruta'
        return ctx


class RutaDeleteView(LoginRequiredMixin, DeleteView):
    model = RutaDia
    template_name = 'routes/confirm_delete.html'
    success_url = reverse_lazy('routes:list')


class RutaDetailView(LoginRequiredMixin, DetailView):
    model = RutaDia
    template_name = 'routes/detail.html'
    context_object_name = 'ruta'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['paradas'] = self.object.paradas.select_related(
            'entrega__cliente',
            'entrega__empresa',
            'entrega__conductor',
        ).order_by('orden')
        ctx['rendicion'] = getattr(self.object, 'rendicion', None)
        return ctx


@login_required
def procesar_foto_ruta(request, pk):
    """
    Procesa la foto con EasyOCR y devuelve lista de clientes detectados.
    """
    ruta = get_object_or_404(RutaDia, pk=pk)
    if not ruta.foto_hoja_ruta:
        return JsonResponse({'error': 'No hay foto subida.'}, status=400)

    lineas = _ocr_extract_names(ruta.foto_hoja_ruta.path)
    texto_completo = '\n'.join(lineas)
    ruta.texto_extraido = texto_completo
    ruta.save(update_fields=['texto_extraido'])

    clientes_encontrados, no_encontrados = _match_clients_from_text(lineas)
    data = {
        'texto_extraido': texto_completo,
        'clientes': [
            {'id': c.pk, 'nombre': c.nombre, 'comuna': c.comuna}
            for c in clientes_encontrados
        ],
        'no_encontrados': no_encontrados,
    }
    return JsonResponse(data)


@login_required
def buscar_por_texto_ruta(request, pk):
    """
    Recibe un texto plano (un nombre por línea) vía POST,
    corre el mismo matching que el OCR y devuelve los clientes encontrados.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido.'}, status=405)
    ruta = get_object_or_404(RutaDia, pk=pk)
    try:
        body = json.loads(request.body)
        texto = body.get('texto', '')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)

    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    if not lineas:
        return JsonResponse({'error': 'El texto está vacío.'}, status=400)

    # Para texto libre usamos un umbral de confianza más alto (0.72):
    # el usuario escribe nombres limpios y sólo deben considerarse "encontrados"
    # los clientes con una coincidencia muy cercana. Así, nombres que no existen
    # en la BD aparecerán siempre en la sección "no encontrados" con botón Registrar.
    clientes_encontrados, no_encontrados = _match_clients_from_text(lineas, umbral=0.72)
    return JsonResponse({
        'clientes': [
            {'id': c.pk, 'nombre': c.nombre, 'comuna': c.comuna}
            for c in clientes_encontrados
        ],
        'no_encontrados': no_encontrados,
    })


@login_required
def buscar_clientes(request):
    """
    Búsqueda JSON de clientes por nombre o comuna (para agregar manualmente).
    """
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'clientes': []})
    clientes = Cliente.objects.filter(
        Q(nombre__icontains=q) | Q(comuna__icontains=q)
    )[:20]
    return JsonResponse({'clientes': [
        {'id': c.pk, 'nombre': c.nombre, 'comuna': c.comuna}
        for c in clientes
    ]})


@login_required
def crear_entregas_desde_ruta(request, pk):
    """
    Recibe lista de cliente_ids → crea una Entrega por cada cliente
    (si no existe ya para esa ruta/fecha) → optimiza las paradas con
    Nearest Neighbor y las guarda en ParadaRuta.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido.'}, status=405)

    ruta = get_object_or_404(RutaDia, pk=pk)

    try:
        body = json.loads(request.body)
        cliente_ids = body.get('cliente_ids', [])
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)

    if not cliente_ids:
        return JsonResponse({'error': 'No se enviaron clientes.'}, status=400)

    clientes = Cliente.objects.filter(pk__in=cliente_ids)
    entregas_creadas = []
    entregas_existentes = []

    entrega_ids_existentes_en_ruta = list(
        ruta.paradas.values_list('entrega_id', flat=True)
    )

    for cliente in clientes:
        entrega, created = Entrega.objects.get_or_create(
            cliente=cliente,
            fecha_programada=ruta.fecha,
            conductor=ruta.conductor,
            defaults={
                'estado': 'pendiente',
                'empresa': ruta.empresa,
            }
        )
        if created:
            entregas_creadas.append(entrega)
        else:
            entregas_existentes.append(entrega)

    entregas_previas = list(Entrega.objects.filter(pk__in=entrega_ids_existentes_en_ruta))
    todas_las_entregas = entregas_previas + entregas_creadas + entregas_existentes

    # Evitar duplicados manteniendo orden estable
    entregas_unicas = []
    seen_ids = set()
    for entrega in todas_las_entregas:
        if entrega.pk in seen_ids:
            continue
        seen_ids.add(entrega.pk)
        entregas_unicas.append(entrega)
    todas_las_entregas = entregas_unicas

    # Optimizar con Nearest Neighbor
    points = []
    for e in todas_las_entregas:
        c = e.cliente
        if c.latitud and c.longitud:
            points.append({
                'id': e.pk,
                'lat': float(c.latitud),
                'lon': float(c.longitud),
                'nombre': c.nombre,
            })

    if len(points) >= 2:
        ordered_ids = _nearest_neighbor_route(points)
    else:
        ordered_ids = [e.pk for e in todas_las_entregas]

    # Guardar paradas: solo reemplaza las de esta ruta
    ruta.paradas.all().delete()
    paradas_guardadas = []
    for i, eid in enumerate(ordered_ids, start=1):
        try:
            entrega = Entrega.objects.get(pk=eid)
            parada = ParadaRuta.objects.create(ruta=ruta, entrega=entrega, orden=i)
            c = entrega.cliente
            paradas_guardadas.append({
                'orden': i,
                'entrega_id': eid,
                'cliente': c.nombre,
                'comuna': c.comuna,
                'observaciones': c.observaciones or '',
                'empresa': entrega.empresa.nombre if entrega.empresa else '',
                'conductor': entrega.conductor.get_full_name() if entrega.conductor else '',
                'descripcion': entrega.descripcion or '',
                'observacion_entrega': entrega.observacion or '',
                'fecha_programada': entrega.fecha_programada.strftime('%d-%m-%Y') if entrega.fecha_programada else '',
                'fecha_entrega': entrega.fecha_entrega.strftime('%d-%m-%Y %H:%M') if entrega.fecha_entrega else '',
                'estado': entrega.estado,
                'estado_display': entrega.get_estado_display(),
                'lat': float(c.latitud) if c.latitud else None,
                'lon': float(c.longitud) if c.longitud else None,
            })
        except Entrega.DoesNotExist:
            pass

    return JsonResponse({
        'creadas': len(entregas_creadas),
        'existentes': len(entregas_existentes),
        'total_paradas': len(paradas_guardadas),
        'paradas': paradas_guardadas,
    })


@login_required
def optimizar_ruta(request, pk):
    """
    Re-optimiza las paradas existentes de una ruta ya creada.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido.'}, status=405)

    ruta = get_object_or_404(RutaDia, pk=pk)
    paradas_qs = ruta.paradas.select_related('entrega__cliente').all()

    points = []
    for p in paradas_qs:
        c = p.entrega.cliente
        if c.latitud and c.longitud:
            points.append({
                'id': p.entrega.pk,
                'lat': float(c.latitud),
                'lon': float(c.longitud),
                'nombre': c.nombre,
            })

    if len(points) < 2:
        return JsonResponse({'error': 'Se necesitan al menos 2 paradas con coordenadas.'}, status=400)

    ordered_ids = _nearest_neighbor_route(points)

    ruta.paradas.all().delete()
    paradas_guardadas = []
    for i, eid in enumerate(ordered_ids, start=1):
        entrega = Entrega.objects.get(pk=eid)
        ParadaRuta.objects.create(ruta=ruta, entrega=entrega, orden=i)
        c = entrega.cliente
        paradas_guardadas.append({
            'orden': i,
            'entrega_id': eid,
            'cliente': c.nombre,
            'comuna': c.comuna or '–',
            'observaciones': c.observaciones or '',
            'empresa': entrega.empresa.nombre if entrega.empresa else '',
            'conductor': entrega.conductor.get_full_name() if entrega.conductor else '',
            'descripcion': entrega.descripcion or '',
            'observacion_entrega': entrega.observacion or '',
            'fecha_programada': entrega.fecha_programada.strftime('%d-%m-%Y') if entrega.fecha_programada else '',
            'fecha_entrega': entrega.fecha_entrega.strftime('%d-%m-%Y %H:%M') if entrega.fecha_entrega else '',
            'estado': entrega.estado,
            'estado_display': entrega.get_estado_display(),
            'lat': float(c.latitud) if c.latitud else None,
            'lon': float(c.longitud) if c.longitud else None,
        })

    return JsonResponse({'ruta_optimizada': paradas_guardadas, 'total': len(paradas_guardadas)})


# ── Navegación en Vivo ────────────────────────────────────────────────────────

@login_required
def navegacion_ruta(request, pk):
    """
    Vista de navegación en vivo para el conductor.
    Muestra el mapa con todas las paradas y permite re-optimizar desde la
    ubicación actual del dispositivo.
    """
    ruta = get_object_or_404(RutaDia, pk=pk)
    paradas = ruta.paradas.select_related('entrega__cliente').order_by('orden')
    ctx = {
        'ruta': ruta,
        'paradas': paradas,
    }
    return render(request, 'routes/navegacion.html', ctx)


@login_required
def reoptimizar_desde_posicion(request, pk):
    """
    Re-optimiza las paradas de una ruta usando la posición actual del conductor
    como punto de partida del algoritmo Nearest Neighbor.
    Recibe POST JSON: {lat: float, lon: float}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido.'}, status=405)

    ruta = get_object_or_404(RutaDia, pk=pk)

    try:
        body = json.loads(request.body)
        lat_actual = float(body.get('lat', 0))
        lon_actual = float(body.get('lon', 0))
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Datos de posición inválidos.'}, status=400)

    paradas_qs = ruta.paradas.select_related('entrega__cliente').all()
    if not paradas_qs.exists():
        return JsonResponse({'error': 'La ruta no tiene paradas.'}, status=400)

    # Punto origen: posición actual del conductor
    points = [{'id': 'origen', 'lat': lat_actual, 'lon': lon_actual}]
    for p in paradas_qs:
        c = p.entrega.cliente
        if c.latitud and c.longitud:
            points.append({
                'id': p.entrega.pk,
                'lat': float(c.latitud),
                'lon': float(c.longitud),
                'nombre': c.nombre,
                'estado': p.entrega.estado,
            })

    # Solo re-optimizar las que no están entregadas
    pendientes = [p for p in points[1:] if p.get('estado') != 'entregado']
    entregadas = [p for p in points[1:] if p.get('estado') == 'entregado']

    if len(pendientes) >= 2:
        # Re-run Nearest Neighbor desde posición actual
        all_points = [points[0]] + pendientes
        ordered_ids = _nearest_neighbor_route(all_points)[1:]  # quitar origen
    elif len(pendientes) == 1:
        ordered_ids = [pendientes[0]['id']]
    else:
        return JsonResponse({'mensaje': 'Todas las entregas están completadas.', 'paradas': []})

    # Reordenar paradas en BD
    ruta.paradas.all().delete()
    orden = 1
    nueva_lista = []

    for eid in ordered_ids:
        try:
            entrega = Entrega.objects.get(pk=eid)
            ParadaRuta.objects.create(ruta=ruta, entrega=entrega, orden=orden)
            c = entrega.cliente
            nueva_lista.append({
                'orden': orden,
                'entrega_id': eid,
                'cliente': c.nombre,
                'comuna': c.comuna or '–',
                'observaciones': c.observaciones or '',
                'empresa': entrega.empresa.nombre if entrega.empresa else '',
                'conductor': entrega.conductor.get_full_name() if entrega.conductor else '',
                'descripcion': entrega.descripcion or '',
                'observacion_entrega': entrega.observacion or '',
                'fecha_programada': entrega.fecha_programada.strftime('%d-%m-%Y') if entrega.fecha_programada else '',
                'fecha_entrega': entrega.fecha_entrega.strftime('%d-%m-%Y %H:%M') if entrega.fecha_entrega else '',
                'estado': entrega.estado,
                'estado_display': entrega.get_estado_display(),
                'lat': float(c.latitud) if c.latitud else None,
                'lon': float(c.longitud) if c.longitud else None,
                'waze': c.url_waze if c.tiene_coordenadas else None,
                'gmaps': c.url_google_maps if c.tiene_coordenadas else None,
            })
            orden += 1
        except Entrega.DoesNotExist:
            pass

    # Re-agregar las ya entregadas al final (sin cambiar BD)
    for p_data in entregadas:
        try:
            entrega = Entrega.objects.get(pk=p_data['id'])
            ParadaRuta.objects.create(ruta=ruta, entrega=entrega, orden=orden)
            c = entrega.cliente
            nueva_lista.append({
                'orden': orden,
                'entrega_id': p_data['id'],
                'cliente': c.nombre,
                'comuna': c.comuna or '–',
                'observaciones': c.observaciones or '',
                'empresa': entrega.empresa.nombre if entrega.empresa else '',
                'conductor': entrega.conductor.get_full_name() if entrega.conductor else '',
                'descripcion': entrega.descripcion or '',
                'observacion_entrega': entrega.observacion or '',
                'fecha_programada': entrega.fecha_programada.strftime('%d-%m-%Y') if entrega.fecha_programada else '',
                'fecha_entrega': entrega.fecha_entrega.strftime('%d-%m-%Y %H:%M') if entrega.fecha_entrega else '',
                'estado': entrega.estado,
                'estado_display': entrega.get_estado_display(),
                'lat': float(c.latitud) if c.latitud else None,
                'lon': float(c.longitud) if c.longitud else None,
                'waze': c.url_waze if c.tiene_coordenadas else None,
                'gmaps': c.url_google_maps if c.tiene_coordenadas else None,
            })
            orden += 1
        except Entrega.DoesNotExist:
            pass

    return JsonResponse({'paradas': nueva_lista, 'total': len(nueva_lista)})


@login_required
def actualizar_estado_parada(request, pk):
    """
    Actualiza el estado de una Entrega directamente desde la navegación.
    POST JSON: {entrega_id: int, estado: str}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido.'}, status=405)

    ruta = get_object_or_404(RutaDia, pk=pk)

    try:
        body = json.loads(request.body)
        entrega_id = int(body.get('entrega_id'))
        nuevo_estado = body.get('estado')
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Datos inválidos.'}, status=400)

    estados_validos = [e[0] for e in Entrega.ESTADO_CHOICES]
    if nuevo_estado not in estados_validos:
        return JsonResponse({'error': 'Estado no válido.'}, status=400)

    from django.utils import timezone
    get_object_or_404(ParadaRuta, ruta=ruta, entrega_id=entrega_id)
    entrega = get_object_or_404(Entrega, pk=entrega_id)
    entrega.estado = nuevo_estado
    if nuevo_estado == 'entregado':
        if not entrega.fecha_entrega:
            entrega.fecha_entrega = timezone.now()
    else:
        entrega.fecha_entrega = None
    entrega.save(update_fields=['estado', 'fecha_entrega'])

    return JsonResponse({
        'ok': True,
        'estado': entrega.estado,
        'estado_display': entrega.get_estado_display(),
        'fecha_entrega': entrega.fecha_entrega.strftime('%d-%m-%Y %H:%M') if entrega.fecha_entrega else '',
    })
