from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'comuna', 'latitud', 'longitud']
        widgets = {
            'latitud': forms.NumberInput(attrs={'step': 'any', 'placeholder': 'Ej: -33.456789'}),
            'longitud': forms.NumberInput(attrs={'step': 'any', 'placeholder': 'Ej: -70.654321'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['nombre'].widget.attrs['placeholder'] = 'Ej: Juan Pérez'
        self.fields['comuna'].widget.attrs['placeholder'] = 'Ej: Las Condes'

