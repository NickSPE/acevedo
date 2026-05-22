from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Moneda

@receiver(post_migrate)
def crear_monedas_por_defecto(sender, **kwargs):
    if sender.name == "cuentas":
        monedas_defecto = [
            {"codigo": "USD", "nombre": "Dólar estadounidense", "simbolo": "$"},
            {"codigo": "PEN", "nombre": "Sol peruano", "simbolo": "S/"},
            {"codigo": "EUR", "nombre": "Euro", "simbolo": "€"},
        ]

        for moneda in monedas_defecto:
            Moneda.objects.get_or_create(codigo=moneda["codigo"], defaults={
                "nombre": moneda["nombre"],
                "simbolo": moneda["simbolo"],
            })
