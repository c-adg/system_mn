from django import forms
from .models import Cliente, Item , Camiones ,  Empresas , Trabajadores , Itemepp , EstadosdePago

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['Rut', 'cliente', 'telefono', 'obra', 'persona_contacto']
        widgets = {
            'Rut': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'obra': forms.TextInput(attrs={'class': 'form-control'}),
            'persona_contacto': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['cantidad_m3', 'descripcion' , 'moneda', 'precio_unitario','condiciones']
        labels = {
            'cantidad_m3': 'Cantidad (m³)',
        }
        widgets = {
            'cantidad_m3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: hormigon gn20'}), 
            'moneda': forms.Select(attrs={'class': 'form-control'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'condiciones': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: retirar en planta '}), 
        }

#Creamos un widget que sí permite múltiples archivos
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


#Creamos un campo personalizado que maneja varios archivos
class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        # Permite validar una lista de archivos
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return [single_file_clean(data, initial)]



class CamionesForm(forms.ModelForm):
    archivos = MultipleFileField(required=False, label="Documentos (PDFs)")

    class Meta:
        model = Camiones
        fields = ['empresa', 'vehiculo', 'patente', 'descripcion',
                  'revision_tecnica', 'circulacion', 'seguro']
        widgets = {
            'empresa': forms.TextInput(attrs={'class': 'form-select'}),
            'vehiculo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del Vehículo'}),
            'patente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Patente'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción opcional'}),
            'revision_tecnica': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'circulacion': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'seguro': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegura que los campos de fecha se muestren correctamente al editar con su formato correspondiente
        for field_name in ['revision_tecnica', 'circulacion', 'seguro']:
            if self.instance and getattr(self.instance, field_name):
                self.fields[field_name].initial = getattr(self.instance, field_name).strftime('%Y-%m-%d')


class EmpresasForm(forms.ModelForm):
    class Meta:
        model = Empresas
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'})
        }



class TrabajadoresForm(forms.ModelForm):
    class Meta:
        model = Trabajadores
        fields = ['nombre', 'empresa'] 


class ItemeppForm(forms.ModelForm):
    class Meta:
        model = Itemepp
        fields = ['guia', 'fecha_item', 'material', 'cantidad', 'patente' , 'unidad', 'precio_unitario']
        widgets = {
            'guia': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'N° Guía',
                'min': '0'
            }),
            'fecha_item': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                },
                format='%Y-%m-%d'
            ),
            'material': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Material'
            }),
            'patente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Patente'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cantidad',
                'step': '0.01',
                'min': '0'
            }),

            'unidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unidad (ej: m³, kg, etc.)'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Precio Unitario',
                'step': '0.01',
                'min': '0'
            }),
        }

class EstadosdePagoForm(forms.ModelForm):
    class Meta:
        model = EstadosdePago
        fields = ['fecha_emision', 'mes_servicio', 'tipo_servicio']
        widgets = {
            'fecha_emision': forms.DateInput(attrs={'type': 'date'}),
            'mes_servicio': forms.TextInput(attrs={'placeholder': 'Ej: 2DA JUNIO'}),
            'tipo_servicio': forms.TextInput(attrs={'placeholder': 'Ej: HORMIGÓN'}),
        }
