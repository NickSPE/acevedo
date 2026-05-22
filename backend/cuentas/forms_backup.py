# cuentas/forms.py
from django import forms
from .models import SubCuenta, TransferenciaSubCuenta, TransferenciaCuentaPrincipal


class SubCuentaForm(forms.ModelForm):
    # Campo adicional para elegir si es subcuenta personal o de negocio
    TIPO_SUBCUENTA_BASE = (
        ('personal', '👤 Subcuenta Personal - Para organizar mis finanzas personales'),
        ('negocio', '💼 Subcuenta de Negocio - Independiente, para actividades comerciales'),
    )
    
    tipo_subcuenta_base = forms.ChoiceField(
        choices=TIPO_SUBCUENTA_BASE,
        initial='personal',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='¿Qué tipo de subcuenta deseas crear?',
        help_text='• Personal: Se vincula a tu cuenta principal para organizar gastos, ahorros, metas.\n• Negocio: Completamente independiente, para tiendas, freelance, ingresos comerciales.'
    )
    
    # Campo para saldo inicial (solo para subcuentas de negocio)
    saldo_inicial = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        }),
        label='Saldo Inicial',
        help_text='Cantidad a transferir desde tu cuenta principal (solo para subcuentas de negocio)'
    )
    
    class Meta:
        model = SubCuenta
        fields = ['nombre', 'descripcion', 'tipo', 'color', 'meta_objetivo', 'fecha_meta']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Mi Tienda Online, Fondo de Emergencia...'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe el propósito de esta subcuenta...'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'color': forms.HiddenInput(),
            'meta_objetivo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'fecha_meta': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Hacer campos opcionales
        self.fields['descripcion'].required = False
        self.fields['meta_objetivo'].required = False
        self.fields['fecha_meta'].required = False
        self.fields['saldo_inicial'].required = False
        
        # Agregar etiquetas personalizadas
        self.fields['nombre'].label = 'Nombre de la SubCuenta'
        self.fields['descripcion'].label = 'Descripción (Opcional)'
        self.fields['color'].label = 'Color'
        self.fields['meta_objetivo'].label = 'Meta de Ahorro/Ingreso (Opcional)'
        self.fields['fecha_meta'].label = 'Fecha Meta (Opcional)'
        
        # Agregar help_text
        self.fields['color'].help_text = 'Se asignará automáticamente según el tipo'
        self.fields['meta_objetivo'].help_text = 'Monto que quieres alcanzar (opcional)'
        
        # Separar opciones de tipo según personal vs negocio
        tipos_personales = [
            ('ahorro_meta', 'Ahorro para Meta'),
            ('emergencia', 'Fondo de Emergencia'),
            ('inversion', 'Inversiones'),
            ('gastos_fijos', 'Gastos Fijos'),
            ('gastos_variables', 'Gastos Variables'),
            ('entretenimiento', 'Entretenimiento'),
            ('viajes', 'Viajes y Vacaciones'),
            ('educacion', 'Educación y Cursos'),
            ('salud', 'Salud y Bienestar'),
            ('familia', 'Gastos Familiares'),
            ('otros', 'Otros'),
        ]
        
        tipos_negocio = [
            ('tienda_online', 'Tienda Online'),
            ('tienda_fisica', 'Tienda Física'),
            ('servicios_profesionales', 'Servicios Profesionales'),
            ('freelance', 'Trabajo Freelance'),
            ('negocio_propio', 'Negocio Propio'),
            ('ingresos_pasivos', 'Ingresos Pasivos'),
            ('ventas_productos', 'Ventas de Productos'),
            ('consultoria', 'Consultoría'),
            ('alquiler_propiedades', 'Alquiler de Propiedades'),
        ]
        
        # Por defecto mostrar tipos personales
        self.fields['tipo'].choices = tipos_personales
        self.fields['tipo'].label = 'Categoría Personal'
        self.fields['tipo'].help_text = 'Selecciona la categoría que mejor describe esta subcuenta personal'
        
        # Si estamos editando, establecer el tipo de subcuenta base actual
        if self.instance and self.instance.pk:
            if self.instance.es_negocio:
                self.fields['tipo_subcuenta_base'].initial = 'negocio'
                self.fields['tipo'].choices = tipos_negocio
                self.fields['tipo'].label = 'Categoría de Negocio'
                self.fields['tipo'].help_text = 'Selecciona la categoría comercial que mejor describe tu actividad'
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre and len(nombre.strip()) < 2:
            raise forms.ValidationError('El nombre debe tener al menos 2 caracteres.')
        return nombre.strip() if nombre else nombre


class TransferenciaSubCuentaForm(forms.ModelForm):
    class Meta:
        model = TransferenciaSubCuenta
        fields = ['subcuenta_origen', 'subcuenta_destino', 'monto', 'descripcion']
        widgets = {
            'subcuenta_origen': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500'
            }),
            'subcuenta_destino': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500',
                'rows': 3,
                'placeholder': 'Motivo de la transferencia (opcional)...'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Hacer la descripción opcional
        self.fields['descripcion'].required = False
        
        # Si hay un usuario, filtrar las subcuentas por las cuentas del usuario
        if user:
            subcuentas = SubCuenta.objects.filter(id_cuenta__id_usuario=user, activa=True)
            self.fields['subcuenta_origen'].queryset = subcuentas
            self.fields['subcuenta_destino'].queryset = subcuentas
            
        # Agregar etiquetas personalizadas
        self.fields['subcuenta_origen'].label = 'Desde SubCuenta'
        self.fields['subcuenta_destino'].label = 'Hacia SubCuenta'
        self.fields['monto'].label = 'Monto a Transferir ($)'
        self.fields['descripcion'].label = 'Descripción (Opcional)'
        
        # Agregar help_text
        self.fields['monto'].help_text = 'Cantidad a transferir entre subcuentas'
    
    def clean(self):
        cleaned_data = super().clean()
        subcuenta_origen = cleaned_data.get('subcuenta_origen')
        subcuenta_destino = cleaned_data.get('subcuenta_destino')
        monto = cleaned_data.get('monto')
        
        # Validar que las subcuentas sean diferentes
        if subcuenta_origen and subcuenta_destino:
            if subcuenta_origen == subcuenta_destino:
                raise forms.ValidationError('No puedes transferir a la misma subcuenta.')
        
        # Validar que hay suficiente saldo en la subcuenta origen
        if subcuenta_origen and monto:
            if float(monto) > float(subcuenta_origen.saldo):
                raise forms.ValidationError(f'Saldo insuficiente en {subcuenta_origen.nombre}. Saldo disponible: ${subcuenta_origen.saldo:.2f}')
        
        return cleaned_data


class DepositoSubCuentaForm(forms.Form):
    """Formulario para depositar dinero desde la cuenta principal a una subcuenta"""
    monto = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00'
        }),
        label='Monto a Depositar ($)'
    )
    descripcion = forms.CharField(
        max_length=300,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'rows': 3,
            'placeholder': 'Motivo del depósito (opcional)...'
        }),
        label='Descripción (Opcional)'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        cuenta = kwargs.pop('cuenta', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar subcuentas por usuario y cuenta
        if user and cuenta:
            self.fields['subcuenta'].queryset = SubCuenta.objects.filter(
                id_cuenta=cuenta, 
                activa=True
            )
            
            # Agregar help_text con saldo disponible
            saldo_disponible = cuenta.saldo_disponible()
            self.fields['monto'].help_text = f'Saldo disponible en cuenta principal: ${saldo_disponible:.2f}'
    
    def clean(self):
        cleaned_data = super().clean()
        subcuenta = cleaned_data.get('subcuenta')
        monto = cleaned_data.get('monto')
        
        if subcuenta and monto:
            cuenta = subcuenta.id_cuenta
            saldo_disponible = cuenta.saldo_disponible()
            
            if float(monto) > float(saldo_disponible):
                raise forms.ValidationError(f'Saldo insuficiente. Saldo disponible: ${saldo_disponible:.2f}')
        
        return cleaned_data


class RetiroSubCuentaForm(forms.Form):
    """Formulario para retirar dinero de una subcuenta hacia la cuenta principal"""
    monto = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00'
        }),
        label='Monto a Retirar ($)'
    )
    descripcion = forms.CharField(
        max_length=300,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500',
            'rows': 3,
            'placeholder': 'Motivo del retiro (opcional)...'
        }),
        label='Descripción (Opcional)'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        cuenta = kwargs.pop('cuenta', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar subcuentas por usuario y cuenta
        if user and cuenta:
            self.fields['subcuenta'].queryset = SubCuenta.objects.filter(
                id_cuenta=cuenta, 
                activa=True,
                saldo__gt=0  # Solo subcuentas con saldo
            )
    
    def clean(self):
        cleaned_data = super().clean()
        subcuenta = cleaned_data.get('subcuenta')
        monto = cleaned_data.get('monto')
        
        if subcuenta and monto:
            if float(monto) > float(subcuenta.saldo):
                raise forms.ValidationError(f'Saldo insuficiente en {subcuenta.nombre}. Saldo disponible: ${subcuenta.saldo:.2f}')
        
        return cleaned_data


class TransferenciaCuentaPrincipalForm(forms.ModelForm):
    """Formulario para transferencias desde subcuentas hacia cuenta principal"""
    class Meta:
        model = TransferenciaCuentaPrincipal
        fields = ['monto', 'tipo', 'descripcion']
        widgets = {
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
                'required': True
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la transferencia (opcional)...',
                'maxlength': 300
            }),
        }
        labels = {
            'monto': 'Monto a transferir',
            'tipo': 'Tipo de transferencia',
            'descripcion': 'Descripción'
        }

    def __init__(self, *args, **kwargs):
        self.subcuenta = kwargs.pop('subcuenta', None)
        super().__init__(*args, **kwargs)
        
        # Personalizar el campo tipo según el contexto
        if self.subcuenta:
            # Para transferencias desde subcuenta independiente
            self.fields['tipo'].choices = [
                ('deposito', 'Transferir a cuenta principal'),
            ]
            self.fields['tipo'].initial = 'deposito'

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if self.subcuenta and monto:
            if monto > self.subcuenta.saldo:
                raise forms.ValidationError(
                    f'No puedes transferir más de {self.subcuenta.saldo} (saldo disponible)'
                )
            if monto <= 0:
                raise forms.ValidationError('El monto debe ser mayor a 0')
        return monto
