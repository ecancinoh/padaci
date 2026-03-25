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
    ('Chile', 'Chile'),
    ('Estado', 'Estado'),
    ('Santander', 'Santander'),
    ('BCI', 'BCI'),
    ('Scotiabank', 'Scotiabank'),
    ('Itaú', 'Itaú'),
    ('Security', 'Security'),
    ('BICE', 'BICE'),
    ('Falabella', 'Falabella'),
    ('Ripley', 'Ripley'),
    ('Consorcio', 'Consorcio'),
    ('Internacional', 'Internacional'),
    ('BTG', 'BTG'),
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
        self.fields['menos_items'].help_text = 'Automático: suma de A + B + C + D + E + estacionamientos.'
        self.fields['menos_items'].disabled = True
        self.fields['total_dinero_recibir'].help_text = 'Automático: Total consolidado - Menos ítems (A,B,C,D,E + estacionamientos).'
        self.fields['total_dinero_recibir'].disabled = True
        self.fields['facturas_nulas'].help_text = 'Automático: Facturas totales - Facturas entregadas. Puedes editarlo manualmente.'

    def clean(self):
        cleaned_data = super().clean()
        km_inicial = cleaned_data.get('kilometraje_inicial') or Decimal('0')
        km_final = cleaned_data.get('kilometraje_final') or Decimal('0')
        total_km = cleaned_data.get('total_kilometros_recorridos')
        facturas_totales = cleaned_data.get('facturas_totales') or 0
        facturas_entregadas = cleaned_data.get('facturas_entregadas') or 0

        if total_km is None:
            cleaned_data['total_kilometros_recorridos'] = km_final - km_inicial

        # Se autocalcula mientras el usuario no edite manualmente el campo.
        if 'facturas_nulas' not in self.changed_data:
            cleaned_data['facturas_nulas'] = max(facturas_totales - facturas_entregadas, 0)

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

        # Solo conservar valor manual cuando el usuario edita explícitamente
        # el campo de total km. Si no, se recalcula automáticamente.
        instance._preserve_total_km_manual = 'total_kilometros_recorridos' in self.changed_data

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


def _make_inline_formset(model_class, form_class, extra_forms):
    return inlineformset_factory(
        RendicionReparto,
        model_class,
        form=form_class,
        extra=extra_forms,
        can_delete=True,
    )


def build_formsets(data=None, instance=None, ruta=None, clientes_sugeridos=None, initial_data=None):
    ruta_base = ruta
    if not ruta_base and instance and getattr(instance, 'ruta_id', None):
        ruta_base = instance.ruta
    cliente_choices = _cliente_choices_from_ruta(ruta_base)
    clientes_sugeridos = clientes_sugeridos or get_clientes_ruta_nombres(ruta_base)
    initial_data = initial_data or {}

    default_extra = 1

    def extra_for(prefix):
        if data is not None:
            return default_extra
        sugeridos = initial_data.get(prefix) or []
        return max(default_extra, len(sugeridos) + 1)

    credito_documento_formset = _make_inline_formset(
        CreditoDocumentoItem,
        CreditoDocumentoItemForm,
        extra_for('a'),
    )
    devolucion_parcial_formset = _make_inline_formset(
        DevolucionParcialItem,
        DevolucionParcialItemForm,
        extra_for('b'),
    )
    credito_confianza_formset = _make_inline_formset(
        CreditoConfianzaItem,
        CreditoConfianzaItemForm,
        extra_for('c'),
    )
    factura_nula_formset = _make_inline_formset(
        FacturaNulaItem,
        FacturaNulaItemForm,
        extra_for('d'),
    )
    deposito_transferencia_formset = _make_inline_formset(
        DepositoTransferenciaItem,
        DepositoTransferenciaItemForm,
        extra_for('e'),
    )

    formsets = {
        'formset_a': credito_documento_formset(
            data=data,
            instance=instance,
            prefix='a',
            initial=initial_data.get('a'),
            form_kwargs={'cliente_choices': cliente_choices},
        ),
        'formset_b': devolucion_parcial_formset(
            data=data,
            instance=instance,
            prefix='b',
            initial=initial_data.get('b'),
        ),
        'formset_c': credito_confianza_formset(
            data=data,
            instance=instance,
            prefix='c',
            initial=initial_data.get('c'),
            form_kwargs={'clientes_sugeridos': clientes_sugeridos},
        ),
        'formset_d': factura_nula_formset(
            data=data,
            instance=instance,
            prefix='d',
            initial=initial_data.get('d'),
        ),
        'formset_e': deposito_transferencia_formset(
            data=data,
            instance=instance,
            prefix='e',
            initial=initial_data.get('e'),
        ),
    }
    for formset in formsets.values():
        _apply_formset_css(formset)
    return formsets
