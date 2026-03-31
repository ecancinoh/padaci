from django import forms
from django.forms import inlineformset_factory

from .models import RutaDia, ParadaRuta, Entrega, EntregaPago
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
        fields = ['estado', 'estado_pago', 'foto_evidencia']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        self.fields['estado_pago'].choices = [
            choice for choice in self.fields['estado_pago'].choices if choice[0] != 'credito'
        ]

        if self.instance and self.instance.pk and self.instance.estado_pago == 'credito':
            self.initial['estado_pago'] = 'pendiente'


class EntregaPagoForm(forms.ModelForm):
    class Meta:
        model = EntregaPago
        fields = ['metodo', 'monto', 'observacion']
        widgets = {
            'monto': forms.NumberInput(attrs={'min': 0, 'step': 1, 'inputmode': 'numeric'}),
            'observacion': forms.TextInput(attrs={'placeholder': 'Referencia o detalle del pago'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control form-control-sm'})


EntregaPagoFormSet = inlineformset_factory(
    Entrega,
    EntregaPago,
    form=EntregaPagoForm,
    extra=0,
    can_delete=False,
)


def build_entrega_pago_formset(data=None, instance=None):
    formset = EntregaPagoFormSet(data=data, instance=instance, prefix='pagos')
    return formset
