from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .mixins import RolRestringidoMixin
from .models import CustomUser
from .forms import CustomAuthForm, CustomUserCreationForm, CustomUserUpdateForm, PasswordCambioForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    form = CustomAuthForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f'Bienvenido, {user.get_full_name()}')
        return redirect('dashboard:index')
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


class UsuarioListView(RolRestringidoMixin, ListView):
    model = CustomUser
    template_name = 'accounts/list.html'
    context_object_name = 'usuarios'
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(username__icontains=q) | qs.filter(first_name__icontains=q) | qs.filter(last_name__icontains=q)
        return qs


class UsuarioCreateView(RolRestringidoMixin, CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/form.html'
    success_url = reverse_lazy('accounts:list')

    def form_valid(self, form):
        messages.success(self.request, 'Usuario creado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nuevo Usuario'
        return ctx


class UsuarioUpdateView(RolRestringidoMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserUpdateForm
    template_name = 'accounts/form.html'
    success_url = reverse_lazy('accounts:list')

    def form_valid(self, form):
        messages.success(self.request, 'Usuario actualizado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Usuario'
        return ctx


class UsuarioDeleteView(RolRestringidoMixin, DeleteView):
    model = CustomUser
    template_name = 'accounts/confirm_delete.html'
    success_url = reverse_lazy('accounts:list')

    def form_valid(self, form):
        messages.success(self.request, 'Usuario eliminado.')
        return super().form_valid(form)


class UsuarioDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'accounts/detail.html'
    context_object_name = 'usuario'


@login_required
def cambiar_password_view(request):
    form = PasswordCambioForm(user=request.user, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, form.user)
        messages.success(request, 'Contraseña actualizada correctamente.')
        return redirect('accounts:detail', pk=request.user.pk)
    return render(request, 'accounts/cambiar_password.html', {'form': form})
