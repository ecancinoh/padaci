from django import forms
from django.utils import timezone

from accounts.models import CustomUser

from .models import Asistencia


class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = ['usuario', 'fecha', 'estado', 'observacion']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['usuario'].queryset = CustomUser.objects.filter(
            rol__in=['conductor', 'peoneta'],
            activo=True,
        ).order_by('last_name', 'first_name', 'username')
        self.fields['fecha'].initial = timezone.localdate()
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class AsistenciaDiariaFiltroForm(forms.Form):
    VISTA_DIA = 'dia'
    VISTA_SEMANA = 'semana'
    VISTA_MES = 'mes'

    VISTA_CHOICES = [
        (VISTA_DIA, 'Día'),
        (VISTA_SEMANA, 'Semana'),
        (VISTA_MES, 'Mes'),
    ]

    fecha = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        label='Fecha',
    )
    vista = forms.ChoiceField(
        choices=VISTA_CHOICES,
        initial=VISTA_SEMANA,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'}),
        label='Vista',
    )
