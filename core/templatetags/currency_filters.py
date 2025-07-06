from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def currency_symbol(user):
    """Obtiene el símbolo de moneda del usuario"""
    try:
        if user and hasattr(user, 'id_moneda') and user.id_moneda:
            return user.id_moneda.simbolo
        return "$"  # Símbolo por defecto
    except:
        return "$"

@register.filter
def format_currency(amount, user=None):
    """Formatea un monto con el símbolo de moneda del usuario"""
    try:
        # Convertir a Decimal para asegurar precisión
        if isinstance(amount, (int, float, str)):
            amount = Decimal(str(amount))
        
        # Obtener símbolo de moneda
        symbol = "$"  # Por defecto
        if user and hasattr(user, 'id_moneda') and user.id_moneda:
            symbol = user.id_moneda.simbolo
        
        # Formatear con comas para miles
        formatted_amount = f"{amount:,.2f}"
        
        return f"{symbol}{formatted_amount}"
    except:
        return f"${amount}"

@register.simple_tag
def user_currency_symbol(user):
    """Template tag para obtener el símbolo de moneda del usuario"""
    try:
        if user and hasattr(user, 'id_moneda') and user.id_moneda:
            return user.id_moneda.simbolo
        return "$"
    except:
        return "$"

@register.simple_tag
def format_money(amount, user=None):
    """Template tag para formatear dinero con símbolo del usuario"""
    try:
        if isinstance(amount, (int, float, str)):
            amount = Decimal(str(amount))
        
        symbol = "$"
        if user and hasattr(user, 'id_moneda') and user.id_moneda:
            symbol = user.id_moneda.simbolo
        
        formatted_amount = f"{amount:,.2f}"
        return f"{symbol}{formatted_amount}"
    except:
        return f"${amount}"
