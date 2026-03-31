from django import forms
from .models import Cliente

# Comunas de la Región del Libertador General Bernardo O'Higgins (VI Región)
COMUNAS_VI_REGION = [
    ('', '— Selecciona una comuna —'),
    # Provincia de Cachapoal
    ('Coinco', 'Coinco'),
    ('Coltauco', 'Coltauco'),
    ('Doñihue', 'Doñihue'),
    ('Graneros', 'Graneros'),
    ('Las Cabras', 'Las Cabras'),
    ('Machalí', 'Machalí'),
    ('Malloa', 'Malloa'),
    ('Mostazal', 'Mostazal'),
    ('Olivar', 'Olivar'),
    ('Peumo', 'Peumo'),
    ('Pichidegua', 'Pichidegua'),
    ('Quinta de Tilcoco', 'Quinta de Tilcoco'),
    ('Rancagua', 'Rancagua'),
    ('Rengo', 'Rengo'),
    ('Requínoa', 'Requínoa'),
    ('San Vicente', 'San Vicente'),
    # Provincia de Colchagua
    ('Chépica', 'Chépica'),
    ('Chimbarongo', 'Chimbarongo'),
    ('Lolol', 'Lolol'),
    ('Nancagua', 'Nancagua'),
    ('Palmilla', 'Palmilla'),
    ('Peralillo', 'Peralillo'),
    ('Placilla', 'Placilla'),
    ('Pumanque', 'Pumanque'),
    ('San Fernando', 'San Fernando'),
    ('Santa Cruz', 'Santa Cruz'),
    # Provincia de Cardenal Caro
    ('La Estrella', 'La Estrella'),
    ('Litueche', 'Litueche'),
    ('Marchihue', 'Marchihue'),
    ('Navidad', 'Navidad'),
    ('Paredones', 'Paredones'),
    ('Pichilemu', 'Pichilemu'),
]


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'comuna', 'direccion', 'latitud', 'longitud', 'tiempo_estimado_atencion', 'observaciones']
        widgets = {
            'comuna': forms.Select(choices=COMUNAS_VI_REGION),
            'direccion': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ej: Av. Siempre Viva 1234, depto 5B'}),
            'latitud': forms.NumberInput(attrs={'step': 'any', 'placeholder': 'Ej: -33.456789'}),
            'longitud': forms.NumberInput(attrs={'step': 'any', 'placeholder': 'Ej: -70.654321'}),
            'tiempo_estimado_atencion': forms.NumberInput(attrs={'min': 1, 'placeholder': 'Minutos', 'value': 10}),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ej: Dejar en portería, llamar antes de llegar, acceso por calle lateral...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comuna'].required = False
        self.fields['direccion'].required = False
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['nombre'].widget.attrs['placeholder'] = 'Ej: Juan Pérez'

