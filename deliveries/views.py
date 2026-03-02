from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Entrega
from .forms import EntregaForm, EntregaEstadoForm


class EntregaListView(LoginRequiredMixin, ListView):
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


class EntregaCreateView(LoginRequiredMixin, CreateView):
    model = Entrega
    form_class = EntregaForm
    template_name = 'deliveries/form.html'
    success_url = reverse_lazy('deliveries:list')

    def form_valid(self, form):
        messages.success(self.request, 'Entrega registrada exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Registrar Entrega'
        return ctx


class EntregaUpdateView(LoginRequiredMixin, UpdateView):
    model = Entrega
    form_class = EntregaForm
    template_name = 'deliveries/form.html'
    success_url = reverse_lazy('deliveries:list')

    def form_valid(self, form):
        messages.success(self.request, 'Entrega actualizada correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Entrega'
        return ctx


class EntregaDeleteView(LoginRequiredMixin, DeleteView):
    model = Entrega
    template_name = 'deliveries/confirm_delete.html'
    success_url = reverse_lazy('deliveries:list')

    def form_valid(self, form):
        messages.success(self.request, 'Entrega eliminada.')
        return super().form_valid(form)


class EntregaDetailView(LoginRequiredMixin, DetailView):
    model = Entrega
    template_name = 'deliveries/detail.html'
    context_object_name = 'entrega'


@login_required
def actualizar_estado(request, pk):
    """Vista rápida para actualizar el estado de una entrega desde móvil/conductor."""
    entrega = get_object_or_404(Entrega, pk=pk)
    if request.method == 'POST':
        form = EntregaEstadoForm(request.POST, request.FILES, instance=entrega)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.estado == 'entregado' and not obj.fecha_entrega:
                obj.fecha_entrega = timezone.now()
            obj.save()
            messages.success(request, 'Estado actualizado correctamente.')
            return redirect('deliveries:detail', pk=pk)
    else:
        form = EntregaEstadoForm(instance=entrega)
    return render(request, 'deliveries/actualizar_estado.html', {'form': form, 'entrega': entrega})
