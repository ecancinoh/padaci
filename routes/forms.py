from django import forms
from .models import RutaDia, ParadaRuta, Entrega
from accounts.models import CustomUser


class RutaDiaForm(forms.ModelForm):
    class Meta:
        model = RutaDia
        fields = ['fecha', 'empresa', 'conductor', 'peoneta', 'estado', 'total_consolidado', 'foto_hoja_ruta', 'observacion']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'total_consolidado': forms.NumberInput(attrs={'min': 0, 'step': 1}),
            'observacion': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['conductor'].queryset = CustomUser.objects.filter(activo=True, rol='conductor').order_by('first_name', 'last_name')
        self.fields['peoneta'].queryset = CustomUser.objects.filter(activo=True, rol__in=['peoneta', 'conductor']).order_by('first_name', 'last_name')


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
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class EntregaEstadoForm(forms.ModelForm):
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
