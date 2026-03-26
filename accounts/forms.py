from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm, PasswordChangeForm
from .models import CustomUser


class CustomAuthForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Usuario'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Contraseña'}))


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'rol', 'telefono', 'rut', 'foto')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class CustomUserUpdateForm(UserChangeForm):
    password = None

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'rol', 'telefono', 'rut', 'foto', 'activo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class PasswordCambioForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
