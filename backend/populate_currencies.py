# Archivo para insertar datos de monedas comunes

def populate_currencies():
    """
    Función para poblar la tabla de monedas con las monedas más comunes
    """
    from cuentas.models import Moneda
    
    monedas = [
        {'codigo': 'USD', 'nombre': 'Dólar estadounidense', 'simbolo': '$'},
        {'codigo': 'EUR', 'nombre': 'Euro', 'simbolo': '€'},
        {'codigo': 'PEN', 'nombre': 'Sol peruano', 'simbolo': 'S/'},
        {'codigo': 'MXN', 'nombre': 'Peso mexicano', 'simbolo': '$'},
        {'codigo': 'COP', 'nombre': 'Peso colombiano', 'simbolo': '$'},
        {'codigo': 'ARS', 'nombre': 'Peso argentino', 'simbolo': '$'},
        {'codigo': 'CLP', 'nombre': 'Peso chileno', 'simbolo': '$'},
        {'codigo': 'BRL', 'nombre': 'Real brasileño', 'simbolo': 'R$'},
        {'codigo': 'GBP', 'nombre': 'Libra esterlina', 'simbolo': '£'},
        {'codigo': 'CAD', 'nombre': 'Dólar canadiense', 'simbolo': 'C$'},
    ]
    
    for moneda_data in monedas:
        Moneda.objects.get_or_create(
            codigo=moneda_data['codigo'],
            defaults={
                'nombre': moneda_data['nombre'],
                'simbolo': moneda_data['simbolo']
            }
        )
    
    print("✅ Monedas pobladas correctamente")

if __name__ == "__main__":
    import django
    import os
    import sys
    
    # Configurar Django
    sys.path.append('c:/Users/ZUZUKA/AppIngRequisitos')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FinGest.settings')
    django.setup()
    
    populate_currencies()
