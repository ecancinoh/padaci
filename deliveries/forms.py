from django import forms
from .models import Entrega


class EntregaForm(forms.ModelForm):
    class Meta:
        model = Entrega
        fields = [
            'cliente', 'conductor',
            'descripcion', 'estado',
            'fecha_programada', 'fecha_entrega', 'observacion',
            'foto_evidencia',
        ]
        widgets = {
            'fecha_programada': forms.DateInput(attrs={'type': 'date'}),
            'fecha_entrega': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'descripcion': forms.Textarea(attrs={'rows': 2}),
            'observacion': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class EntregaEstadoForm(forms.ModelForm):
    """Formulario simplificado para actualizar solo el estado de una entrega."""

    class Meta:
        model = Entrega
        fields = ['estado', 'observacion', 'foto_evidencia', 'fecha_entrega']
        widgets = {
            'fecha_entrega': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'observacion': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
