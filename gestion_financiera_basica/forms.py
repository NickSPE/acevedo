# gestion_financiera_basica/forms.py
from django import forms
from .models import Movimiento, MetaAhorro, AporteMetaAhorro
from cuentas.models import Cuenta
from usuarios.models import Usuario


class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = ['nombre', 'tipo', 'categoria', 'monto', 'fecha_movimiento', 'descripcion', 'id_cuenta']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nombre de la transacción'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0'
            }),
            'fecha_movimiento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Descripción opcional...'
            }),
            'tipo': forms.RadioSelect(),
            'categoria': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'id': 'id_categoria'
            }),
            'id_cuenta': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Hacer la descripción explícitamente opcional
        self.fields['descripcion'].required = False
        self.fields['descripcion'].help_text = 'Este campo es opcional'
        
        # Configurar el campo de categoría - NO asignar choices aquí
        # El JavaScript se encargará de llenar las opciones dinámicamente
        self.fields['categoria'].required = False
        self.fields['categoria'].widget.choices = [('', 'Seleccionar categoría...')]
        
        # Si hay un usuario, filtrar las cuentas por ese usuario
        if user:
            self.fields['id_cuenta'].queryset = Cuenta.objects.filter(id_usuario=user)
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Asegurar que la descripción no lance errores si está vacía
        descripcion = cleaned_data.get('descripcion')
        if not descripcion:
            cleaned_data['descripcion'] = ''
        
        return cleaned_data


class MetaAhorroForm(forms.ModelForm):
    class Meta:
        model = MetaAhorro
        fields = ['nombre', 'descripcion', 'monto_objetivo', 'fecha_inicio', 'fecha_limite', 'frecuencia_aporte', 'id_cuenta']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nombre de la meta de ahorro'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Describe tu meta de ahorro...'
            }),
            'monto_objetivo': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'fecha_limite': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'frecuencia_aporte': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'id_cuenta': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Si hay un usuario, filtrar las cuentas por ese usuario
        if user:
            self.fields['id_cuenta'].queryset = Cuenta.objects.filter(id_usuario=user)
            
        # Agregar etiquetas personalizadas
        self.fields['nombre'].label = 'Nombre de la Meta'
        self.fields['descripcion'].label = 'Descripción'
        self.fields['monto_objetivo'].label = 'Monto Objetivo ($)'
        self.fields['fecha_inicio'].label = 'Fecha de Inicio'
        self.fields['fecha_limite'].label = 'Fecha Límite'
        self.fields['frecuencia_aporte'].label = 'Frecuencia de Aportes'
        self.fields['id_cuenta'].label = 'Cuenta Asociada'
        
        # Agregar help_text
        self.fields['monto_objetivo'].help_text = 'Cantidad total que deseas ahorrar'
        self.fields['fecha_limite'].help_text = 'Fecha en la que planeas alcanzar tu meta'
        self.fields['frecuencia_aporte'].help_text = 'Con qué frecuencia planeas hacer aportes a esta meta'
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_limite = cleaned_data.get('fecha_limite')
        monto_objetivo = cleaned_data.get('monto_objetivo')
        
        # Validar que la fecha límite sea posterior a la fecha de inicio
        if fecha_inicio and fecha_limite:
            if fecha_limite <= fecha_inicio:
                raise forms.ValidationError('La fecha límite debe ser posterior a la fecha de inicio.')
        
        # Validar que el monto objetivo sea positivo
        if monto_objetivo and monto_objetivo <= 0:
            raise forms.ValidationError('El monto objetivo debe ser mayor a cero.')
        
        return cleaned_data


class AporteMetaAhorroForm(forms.ModelForm):
    class Meta:
        model = AporteMetaAhorro
        fields = ['monto', 'descripcion']
        widgets = {
            'monto': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500',
                'rows': 3,
                'placeholder': 'Descripción del aporte (opcional)...'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        self.meta_ahorro = kwargs.pop('meta_ahorro', None)
        super().__init__(*args, **kwargs)
        
        # Hacer la descripción explícitamente opcional
        self.fields['descripcion'].required = False
        
        # Agregar etiquetas personalizadas
        self.fields['monto'].label = 'Monto del Aporte ($)'
        self.fields['descripcion'].label = 'Descripción (Opcional)'
        
        # Agregar help_text
        if self.meta_ahorro:
            falta = self.meta_ahorro.falta_por_ahorrar()
            self.fields['monto'].help_text = f'Cantidad a aportar. Falta: ${falta:.2f} para alcanzar la meta'
    
    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        
        if monto and monto <= 0:
            raise forms.ValidationError('El monto del aporte debe ser mayor a cero.')
        
        return monto