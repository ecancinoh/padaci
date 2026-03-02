from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .models import Empresa
from .forms import EmpresaForm


class EmpresaListView(LoginRequiredMixin, ListView):
    model = Empresa
    template_name = 'companies/list.html'
    context_object_name = 'empresas'
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(nombre__icontains=q) | qs.filter(rut__icontains=q)
        return qs


class EmpresaCreateView(LoginRequiredMixin, CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'companies/form.html'
    success_url = reverse_lazy('companies:list')

    def form_valid(self, form):
        messages.success(self.request, 'Empresa creada exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva Empresa'
        return ctx


class EmpresaUpdateView(LoginRequiredMixin, UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'companies/form.html'
    success_url = reverse_lazy('companies:list')

    def form_valid(self, form):
        messages.success(self.request, 'Empresa actualizada correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Empresa'
        return ctx


class EmpresaDeleteView(LoginRequiredMixin, DeleteView):
    model = Empresa
    template_name = 'companies/confirm_delete.html'
    success_url = reverse_lazy('companies:list')

    def form_valid(self, form):
        messages.success(self.request, 'Empresa eliminada.')
        return super().form_valid(form)


class EmpresaDetailView(LoginRequiredMixin, DetailView):
    model = Empresa
    template_name = 'companies/detail.html'
    context_object_name = 'empresa'
