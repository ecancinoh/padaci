from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .models import Cliente
from .forms import ClienteForm


class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'clients/list.html'
    context_object_name = 'clientes'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '')
        empresa = self.request.GET.get('empresa', '')
        sin_coordenadas = self.request.GET.get('sin_coordenadas')
        if q:
            qs = qs.filter(nombre__icontains=q) | qs.filter(comuna__icontains=q)
        if empresa:
            qs = qs.filter(empresa_id=empresa)
        if sin_coordenadas:
            qs = qs.filter(activo=True).filter(latitud__isnull=True) | qs.filter(activo=True).filter(longitud__isnull=True).exclude(latitud__isnull=True)
        return qs


class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clients/form.html'
    success_url = reverse_lazy('clients:list')

    def get_initial(self):
        initial = super().get_initial()
        nombre = self.request.GET.get('nombre', '').strip()
        if nombre:
            initial['nombre'] = nombre
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Cliente creado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nuevo Cliente'
        return ctx


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clients/form.html'
    success_url = reverse_lazy('clients:list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Cliente'
        return ctx



from accounts.mixins import RolRestringidoMixin


from routes.models import ParadaRuta, Entrega, RutaDia
from django.db import transaction

class ClienteDeleteView(RolRestringidoMixin, LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'clients/confirm_delete.html'
    success_url = reverse_lazy('clients:list')

    def form_valid(self, form):
        cliente = self.object
        entregas = Entrega.objects.filter(cliente=cliente)
        # Buscar todas las entregas del cliente que tengan al menos una parada en una ruta planificada
        entregas_con_parada_planificada = entregas.filter(
            paradas__ruta__estado='planificada'
        ).distinct()
        # IDs de esas entregas
        entregas_ids = list(entregas_con_parada_planificada.values_list('id', flat=True))
        # Todas las paradas de esas entregas en rutas planificadas
        paradas_planificadas = ParadaRuta.objects.filter(
            entrega_id__in=entregas_ids,
            ruta__estado='planificada'
        )
        paradas_ids = list(paradas_planificadas.values_list('id', flat=True))

        with transaction.atomic():
            # Eliminar paradas y entregas asociadas a rutas planificadas usando listas de IDs
            if paradas_ids:
                ParadaRuta.objects.filter(id__in=paradas_ids).delete()
            if entregas_ids:
                Entrega.objects.filter(id__in=entregas_ids).delete()

            # Verificar si quedan entregas asociadas al cliente
            entregas_restantes = Entrega.objects.filter(cliente=cliente)
            if entregas_restantes.exists():
                detalles = '\n'.join([str(e) for e in entregas_restantes])
                messages.error(self.request, f'No se puede eliminar el cliente porque tiene entregas asociadas en rutas que no están en estado Planificada o sin ruta.\nEntregas que lo impiden:\n{detalles}')
                transaction.set_rollback(True)
                return self.form_invalid(form)

            # Ahora eliminar el cliente
            response = super().form_valid(form)
        messages.success(self.request, 'Cliente y entregas asociadas en rutas planificadas eliminados correctamente.')
        return response


class ClienteDetailView(LoginRequiredMixin, DetailView):
    model = Cliente
    template_name = 'clients/detail.html'
    context_object_name = 'cliente'
