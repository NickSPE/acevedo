# cuentas/forms.py
from django import forms
from .models import SubCuenta, TransferenciaSubCuenta, TransferenciaCuentaPrincipal


class SubCuentaForm(forms.ModelForm):
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
        help_text='Cantidad a transferir desde tu cuenta principal'
    )
    
    tipo_subcuenta = forms.CharField(
        required=False,
        initial='personal',
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = SubCuenta
        fields = ['nombre', 'descripcion', 'tipo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Ahorros para vacaciones, Mi negocio...'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe el propósito de esta subcuenta...'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Hacer campos opcionales
        self.fields['descripcion'].required = False
        self.fields['saldo_inicial'].required = False
        
        # Agregar etiquetas personalizadas
        self.fields['nombre'].label = 'Nombre de la subcuenta'
        self.fields['descripcion'].label = 'Descripción (opcional)'
        self.fields['tipo'].label = 'Categoría'
        
        # Todas las opciones de categoría (personales y de negocio)
        self.fields['tipo'].choices = [
            ('', 'Selecciona una categoría'),
            # Categorías personales
            ('ahorros', 'Ahorros'),
            ('emergencia', 'Fondo de Emergencia'),
            ('gastos_fijos', 'Gastos Fijos'),
            ('gastos_variables', 'Gastos Variables'),
            ('entretenimiento', 'Entretenimiento'),
            ('viajes', 'Viajes'),
            ('educacion', 'Educación'),
            ('salud', 'Salud'),
            ('familia', 'Familia'),
            ('inversion', 'Inversiones'),
            ('otros', 'Otros'),
            # Categorías de negocio
            ('tienda_fisica', 'Tienda Física'),
            ('tienda_online', 'Tienda Online'),
            ('servicios', 'Servicios Profesionales'),
            ('freelance', 'Trabajo Freelance'),
            ('consultoria', 'Consultoría'),
            ('ventas', 'Ventas'),
            ('marketing', 'Marketing y Publicidad'),
            ('inventario', 'Inventario'),
            ('gastos_operativos', 'Gastos Operativos'),
            ('equipamiento', 'Equipamiento'),
            ('otros_negocio', 'Otros (Negocio)'),
        ]


class TransferenciaSubCuentaForm(forms.ModelForm):
    class Meta:
        model = TransferenciaSubCuenta
        fields = ['subcuenta_origen', 'subcuenta_destino', 'monto', 'descripcion']
        widgets = {
            'subcuenta_origen': forms.Select(attrs={
                'class': 'form-control'
            }),
            'subcuenta_destino': forms.Select(attrs={
                'class': 'form-control'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Motivo de la transferencia (opcional)...'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Hacer descripción opcional
        self.fields['descripcion'].required = False
        
        # Personalizar etiquetas
        self.fields['subcuenta_origen'].label = 'Desde subcuenta'
        self.fields['subcuenta_destino'].label = 'Hacia subcuenta'
        self.fields['monto'].label = 'Monto a transferir'
        self.fields['descripcion'].label = 'Descripción (opcional)'
        
        # Filtrar subcuentas del usuario si se proporciona
        if self.user:
            from django.db.models import Q
            subcuentas = SubCuenta.objects.filter(
                Q(id_cuenta__id_usuario=self.user) | Q(propietario=self.user),
                activa=True
            )
            choices = [('', 'Selecciona una subcuenta')]
            choices.extend([(sub.id, f"{sub.nombre} (${sub.saldo})") for sub in subcuentas])
            
            self.fields['subcuenta_origen'].choices = choices
            self.fields['subcuenta_destino'].choices = choices


class DepositoSubCuentaForm(forms.Form):
    monto = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border-2 border-[#E5E1DD] rounded-lg focus:outline-none focus:border-[#227C91] text-[#605952]',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00'
        }),
        label='Monto a depositar'
    )
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border-2 border-[#E5E1DD] rounded-lg focus:outline-none focus:border-[#227C91] text-[#605952] resize-none',
            'rows': 3,
            'placeholder': 'Motivo del depósito (opcional)...'
        }),
        label='Descripción (opcional)'
    )


class RetiroSubCuentaForm(forms.Form):
    monto = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border-2 border-[#E5E1DD] rounded-lg focus:outline-none focus:border-[#227C91] text-[#605952]',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00'
        }),
        label='Monto a retirar'
    )
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border-2 border-[#E5E1DD] rounded-lg focus:outline-none focus:border-[#227C91] text-[#605952] resize-none',
            'rows': 3,
            'placeholder': 'Motivo del retiro (opcional)...'
        }),
        label='Descripción (opcional)'
    )


class TransferenciaCuentaPrincipalForm(forms.ModelForm):
    TIPO_CHOICES = [
        ('deposito', 'Transferir hacia cuenta principal'),
        ('retiro', 'Transferir hacia subcuenta'),
    ]
    
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='deposito'
    )
    
    class Meta:
        model = TransferenciaCuentaPrincipal
        fields = ['tipo', 'monto', 'descripcion']
        widgets = {
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Motivo de la transferencia (opcional)...'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.subcuenta = kwargs.pop('subcuenta', None)
        super().__init__(*args, **kwargs)
        
        # Hacer descripción opcional
        self.fields['descripcion'].required = False
        
        # Personalizar etiquetas
        self.fields['tipo'].label = 'Tipo de transferencia'
        self.fields['monto'].label = 'Monto a transferir'
        self.fields['descripcion'].label = 'Descripción (opcional)'
        
        # Validar monto máximo según el tipo
        if self.subcuenta and 'tipo' in self.data and self.data['tipo'] == 'deposito':
            # Transferir de subcuenta a cuenta principal
            max_amount = self.subcuenta.saldo
            self.fields['monto'].widget.attrs['max'] = str(max_amount)
            self.fields['monto'].help_text = f'Máximo disponible: ${max_amount:.2f}'
    
    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        tipo = self.cleaned_data.get('tipo')
        
        if not monto or monto <= 0:
            raise forms.ValidationError('El monto debe ser mayor a 0')
        
        if self.subcuenta and tipo == 'deposito':
            # Validar que hay suficiente saldo en la subcuenta
            if monto > self.subcuenta.saldo:
                raise forms.ValidationError(f'No hay suficiente saldo en la subcuenta. Disponible: ${self.subcuenta.saldo:.2f}')
        
        return monto
