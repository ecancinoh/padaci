from django import forms
from django.forms import inlineformset_factory
from decimal import Decimal
from companies.models import Empresa
from accounts.models import CustomUser
from .models import (
    RendicionReparto,
    CreditoDocumentoItem,
    DevolucionParcialItem,
    CreditoConfianzaItem,
    FacturaNulaItem,
    DepositoTransferenciaItem,
)


CHILE_BANK_CHOICES = [
    ('Banco de Chile', 'Banco de Chile'),
    ('BancoEstado', 'BancoEstado'),
    ('Banco Santander Chile', 'Banco Santander Chile'),
    ('Banco de Crédito e Inversiones (BCI)', 'Banco de Crédito e Inversiones (BCI)'),
    ('Scotiabank Chile', 'Scotiabank Chile'),
    ('Itaú Corpbanca', 'Itaú Corpbanca'),
    ('Banco Security', 'Banco Security'),
    ('Banco BICE', 'Banco BICE'),
    ('Banco Falabella', 'Banco Falabella'),
    ('Banco Ripley', 'Banco Ripley'),
    ('Banco Consorcio', 'Banco Consorcio'),
    ('Banco Internacional', 'Banco Internacional'),
    ('Banco BTG Pactual Chile', 'Banco BTG Pactual Chile'),
]


def _cliente_choices_from_ruta(ruta):
    if not ruta:
        return []
    nombres = []
    seen = set()
    paradas = ruta.paradas.select_related('entrega__cliente').all()
    for parada in paradas:
        nombre = parada.entrega.cliente.nombre
        if nombre and nombre not in seen:
            seen.add(nombre)
            nombres.append((nombre, nombre))
    return nombres


def get_clientes_ruta_nombres(ruta):
    return [nombre for nombre, _ in _cliente_choices_from_ruta(ruta)]


class RendicionRepartoForm(forms.ModelForm):
    distribuidora = forms.ModelChoiceField(
        queryset=Empresa.objects.none(),
        required=False,
        label='Distribuidora',
    )
    nombre_repartidor = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(),
        required=True,
        label='Repartidor',
    )
    nombre_peoneta = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(),
        required=False,
        label='Peoneta',
    )

    class Meta:
        model = RendicionReparto
        fields = [
            'ruta',
            'fecha',
            'distribuidora',
            'nombre_repartidor',
            'nombre_peoneta',
            'estacionamientos',
            'diferencia_menos',
            'diferencia_mas',
            'total_consolidado',
            'menos_items',
            'total_dinero_recibir',
            'facturas_totales',
            'facturas_entregadas',
            'facturas_nulas',
            'kilometraje_inicial',
            'kilometraje_final',
            'total_kilometros_recorridos',
        ]
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        empresas_qs = Empresa.objects.filter(activa=True).order_by('nombre')
        conductores_qs = CustomUser.objects.filter(activo=True, rol='conductor').order_by('first_name', 'last_name', 'username')
        peonetas_qs = CustomUser.objects.filter(activo=True, rol__in=['peoneta', 'conductor']).order_by('first_name', 'last_name', 'username')

        self.fields['distribuidora'].queryset = empresas_qs
        self.fields['nombre_repartidor'].queryset = conductores_qs
        self.fields['nombre_peoneta'].queryset = peonetas_qs

        if self.instance and self.instance.pk:
            if self.instance.fecha:
                self.initial['fecha'] = self.instance.fecha.strftime('%Y-%m-%d')
            if self.instance.ruta_id:
                self.initial['total_consolidado'] = self.instance.ruta.total_consolidado

            distribuidora_id = None
            repartidor_id = None
            peoneta_id = None

            if self.instance.ruta_id:
                if self.instance.ruta.empresa_id:
                    distribuidora_id = self.instance.ruta.empresa_id
                repartidor_id = self.instance.ruta.conductor_id
                peoneta_id = self.instance.ruta.peoneta_id

            if not distribuidora_id and self.instance.distribuidora:
                empresa_match = Empresa.objects.filter(nombre=self.instance.distribuidora).first()
                if empresa_match:
                    distribuidora_id = empresa_match.pk

            if not repartidor_id and self.instance.nombre_repartidor:
                for user in conductores_qs:
                    etiqueta = user.get_full_name() or user.username
                    if etiqueta == self.instance.nombre_repartidor:
                        repartidor_id = user.pk
                        break

            if not peoneta_id and self.instance.nombre_peoneta:
                for user in peonetas_qs:
                    etiqueta = user.get_full_name() or user.username
                    if etiqueta == self.instance.nombre_peoneta:
                        peoneta_id = user.pk
                        break

            if distribuidora_id:
                self.initial['distribuidora'] = distribuidora_id
            if repartidor_id:
                self.initial['nombre_repartidor'] = repartidor_id
            if peoneta_id:
                self.initial['nombre_peoneta'] = peoneta_id

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if isinstance(field, (forms.DecimalField, forms.IntegerField)):
                field.widget.attrs.update({'min': 0})
        self.fields['ruta'].queryset = self.fields['ruta'].queryset.select_related('conductor', 'empresa')
        self.fields['total_kilometros_recorridos'].required = False
        self.fields['total_kilometros_recorridos'].help_text = 'Automático (Kilometraje final - Kilometraje inicial), editable manualmente si se requiere.'
        self.fields['total_consolidado'].help_text = 'Se trae automáticamente desde Total consolidado de la Ruta del Día.'
        self.fields['total_consolidado'].disabled = True
        self.fields['menos_items'].help_text = 'Automático: suma de A + B + C + D + E.'
        self.fields['menos_items'].disabled = True
        self.fields['total_dinero_recibir'].help_text = 'Automático: Total consolidado - Menos ítems (A,B,C,D,E).'
        self.fields['total_dinero_recibir'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        km_inicial = cleaned_data.get('kilometraje_inicial') or Decimal('0')
        km_final = cleaned_data.get('kilometraje_final') or Decimal('0')
        total_km = cleaned_data.get('total_kilometros_recorridos')

        if total_km is None:
            cleaned_data['total_kilometros_recorridos'] = km_final - km_inicial

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        empresa = self.cleaned_data.get('distribuidora')
        repartidor = self.cleaned_data.get('nombre_repartidor')
        peoneta = self.cleaned_data.get('nombre_peoneta')

        instance.distribuidora = empresa.nombre if empresa else ''
        instance.nombre_repartidor = (repartidor.get_full_name() or repartidor.username) if repartidor else ''
        instance.nombre_peoneta = (peoneta.get_full_name() or peoneta.username) if peoneta else ''
        if instance.ruta_id:
            instance.total_consolidado = instance.ruta.total_consolidado

        total_km_raw = ''
        if self.is_bound:
            total_km_raw = (self.data.get(self.add_prefix('total_kilometros_recorridos')) or '').strip()
        instance._preserve_total_km_manual = bool(total_km_raw)

        if commit:
            instance.save()
        return instance


class CreditoDocumentoItemForm(forms.ModelForm):
    nombre_cliente = forms.ChoiceField(choices=[], required=False, label='Nombre cliente')
    banco = forms.ChoiceField(choices=[], required=False, label='Banco')

    class Meta:
        model = CreditoDocumentoItem
        fields = ['numero_factura', 'nombre_cliente', 'monto', 'banco']

    def __init__(self, *args, **kwargs):
        cliente_choices = kwargs.pop('cliente_choices', [])
        super().__init__(*args, **kwargs)
        current_value = self.instance.nombre_cliente if self.instance and self.instance.pk else None
        choices = [('', '---------')] + list(cliente_choices)
        if current_value and current_value not in [c[0] for c in choices]:
            choices.append((current_value, current_value))
        self.fields['nombre_cliente'].choices = choices

        banco_value = self.instance.banco if self.instance and self.instance.pk else None
        banco_choices = [('', '---------')] + list(CHILE_BANK_CHOICES)
        if banco_value and banco_value not in [b[0] for b in banco_choices]:
            banco_choices.append((banco_value, banco_value))
        self.fields['banco'].choices = banco_choices


class DevolucionParcialItemForm(forms.ModelForm):
    class Meta:
        model = DevolucionParcialItem
        fields = ['numero_factura', 'motivo', 'monto']


class CreditoConfianzaItemForm(forms.ModelForm):
    class Meta:
        model = CreditoConfianzaItem
        fields = ['numero_factura', 'autoriza_credito', 'monto']

    def __init__(self, *args, **kwargs):
        clientes_sugeridos = kwargs.pop('clientes_sugeridos', [])
        super().__init__(*args, **kwargs)
        self.fields['autoriza_credito'].widget = forms.TextInput(attrs={
            'list': 'autoriza-clientes-list',
            'placeholder': 'Escribe o selecciona un cliente de la ruta',
        })


class FacturaNulaItemForm(forms.ModelForm):
    class Meta:
        model = FacturaNulaItem
        fields = ['numero_factura', 'monto']


class DepositoTransferenciaItemForm(forms.ModelForm):
    class Meta:
        model = DepositoTransferenciaItem
        fields = ['numero_factura', 'monto']


def _apply_formset_css(formset):
    for form in formset.forms:
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control form-control-sm'})


CreditoDocumentoFormSet = inlineformset_factory(
    RendicionReparto,
    CreditoDocumentoItem,
    form=CreditoDocumentoItemForm,
    extra=8,
    can_delete=True,
)

DevolucionParcialFormSet = inlineformset_factory(
    RendicionReparto,
    DevolucionParcialItem,
    form=DevolucionParcialItemForm,
    extra=8,
    can_delete=True,
)

CreditoConfianzaFormSet = inlineformset_factory(
    RendicionReparto,
    CreditoConfianzaItem,
    form=CreditoConfianzaItemForm,
    extra=8,
    can_delete=True,
)

FacturaNulaFormSet = inlineformset_factory(
    RendicionReparto,
    FacturaNulaItem,
    form=FacturaNulaItemForm,
    extra=8,
    can_delete=True,
)

DepositoTransferenciaFormSet = inlineformset_factory(
    RendicionReparto,
    DepositoTransferenciaItem,
    form=DepositoTransferenciaItemForm,
    extra=8,
    can_delete=True,
)


def build_formsets(data=None, instance=None, ruta=None, clientes_sugeridos=None):
    ruta_base = ruta
    if not ruta_base and instance and getattr(instance, 'ruta_id', None):
        ruta_base = instance.ruta
    cliente_choices = _cliente_choices_from_ruta(ruta_base)
    clientes_sugeridos = clientes_sugeridos or get_clientes_ruta_nombres(ruta_base)

    formsets = {
        'formset_a': CreditoDocumentoFormSet(
            data=data,
            instance=instance,
            prefix='a',
            form_kwargs={'cliente_choices': cliente_choices},
        ),
        'formset_b': DevolucionParcialFormSet(data=data, instance=instance, prefix='b'),
        'formset_c': CreditoConfianzaFormSet(
            data=data,
            instance=instance,
            prefix='c',
            form_kwargs={'clientes_sugeridos': clientes_sugeridos},
        ),
        'formset_d': FacturaNulaFormSet(data=data, instance=instance, prefix='d'),
        'formset_e': DepositoTransferenciaFormSet(data=data, instance=instance, prefix='e'),
    }
    for formset in formsets.values():
        _apply_formset_css(formset)
    return formsets
