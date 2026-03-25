from django import forms

from .models import PlanificacionSemanal


class PlanificacionSemanalForm(forms.ModelForm):
    class Meta:
        model = PlanificacionSemanal
        fields = [
            'nombre',
            'max_horas_jornada',
            'velocidad_promedio_kmh',
            'minutos_servicio_por_cliente',
            'capacidad_lunes',
            'capacidad_martes',
            'capacidad_miercoles',
            'capacidad_jueves',
            'capacidad_viernes',
            'activo',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Semana zona norte'}),
            'max_horas_jornada': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'step': '0.1'}),
            'velocidad_promedio_kmh': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'step': '0.1'}),
            'minutos_servicio_por_cliente': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'capacidad_lunes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'capacidad_martes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'capacidad_miercoles': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'capacidad_jueves': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'capacidad_viernes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned = super().clean()
        horas = cleaned.get('max_horas_jornada')
        velocidad = cleaned.get('velocidad_promedio_kmh')
        minutos = cleaned.get('minutos_servicio_por_cliente')

        if horas is not None and horas <= 0:
            self.add_error('max_horas_jornada', 'Debe ser mayor a 0.')
        if velocidad is not None and velocidad <= 0:
            self.add_error('velocidad_promedio_kmh', 'Debe ser mayor a 0.')
        if minutos is not None and minutos <= 0:
            self.add_error('minutos_servicio_por_cliente', 'Debe ser mayor a 0.')
        return cleaned
