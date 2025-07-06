# cuentas/forms.py
from django import forms
from .models import SubCuenta, TransferenciaSubCuenta


class SubCuentaForm(forms.ModelForm):
    class Meta:
        model = SubCuenta
        fields = ['nombre', 'descripcion', 'saldo', 'tipo', 'color', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nombre de la subcuenta'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Describe el propósito de esta subcuenta...'
            }),
            'saldo': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'tipo': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'color': forms.HiddenInput(),
            'activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer campos opcionales
        self.fields['descripcion'].required = False
        
        # Agregar etiquetas personalizadas
        self.fields['nombre'].label = 'Nombre de la SubCuenta'
        self.fields['descripcion'].label = 'Descripción (Opcional)'
        self.fields['tipo'].label = 'Tipo de SubCuenta'
        self.fields['color'].label = 'Color'
        
        # Agregar help_text
        self.fields['tipo'].help_text = 'Categoría que mejor describe esta subcuenta'
        self.fields['color'].help_text = 'Color para identificar fácilmente esta subcuenta'
    
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
