from django import forms
from clients.models import Cliente
from .models import DeliveryConfig

class DeliveryConfigForm(forms.ModelForm):
    days_of_week = forms.MultipleChoiceField(
        choices=[
            ("mon", "Lunes"),
            ("tue", "Martes"),
            ("wed", "Miércoles"),
            ("thu", "Jueves"),
            ("fri", "Viernes"),
            ("sat", "Sábado"),
            ("sun", "Domingo"),
        ],
        widget=forms.CheckboxSelectMultiple,
        label="Días de la semana para repartir"
    )
    clients = forms.ModelMultipleChoiceField(
        queryset=Cliente.objects.filter(activo=True),
        widget=forms.SelectMultiple,
        label="Clientes a repartir"
    )
    num_vehicles = forms.IntegerField(min_value=1, label="Cantidad de vehículos disponibles")

    class Meta:
        model = DeliveryConfig
        fields = ["days_of_week", "clients", "num_vehicles"]
