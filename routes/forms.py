from django import forms
from .models import RutaDia, ParadaRuta


class RutaDiaForm(forms.ModelForm):
    class Meta:
        model = RutaDia
        fields = ['fecha', 'empresa', 'conductor', 'estado', 'foto_hoja_ruta', 'observacion']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'observacion': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class ParadaRutaForm(forms.ModelForm):
    class Meta:
        model = ParadaRuta
        fields = ['entrega', 'orden', 'hora_estimada', 'distancia_anterior_km']
        widgets = {
            'hora_estimada': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
