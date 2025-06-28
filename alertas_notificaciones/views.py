from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

def get_relative_time(timestamp):
    now = timezone.now()
    diff = now - timestamp
    minutes = int(diff.total_seconds() // 60)
    if minutes < 1:
        return "hace un momento"
    if minutes < 60:
        return f"hace {minutes} min"
    hours = minutes // 60
    if hours < 24:
        return f"hace {hours}h"
    days = hours // 24
    if days < 7:
        return f"hace {days}d"
    return timestamp.strftime("%d/%m/%Y")

def notification_history(request):
    # Ejemplo de notificaciones (simula lo que recibes en React)
    notifications = [
        {
            "id": "1",
            "type": "critical",
            "title": "Fondos Insuficientes",
            "message": "Tu cuenta principal tiene un saldo bajo",
            "timestamp": timezone.now() - timedelta(minutes=5),
            "read": False,
            "category": "Saldo",
            "action": "Recargar",
        },
        {
            "id": "2",
            "type": "warning",
            "title": "Presupuesto Excedido",
            "message": "Has superado el 90% de tu presupuesto en Alimentación",
            "timestamp": timezone.now() - timedelta(hours=2),
            "read": False,
            "category": "Presupuesto",
            "action": None,
        },
        {
            "id": "3",
            "type": "info",
            "title": "Meta Alcanzada",
            "message": "¡Felicidades! Has completado tu meta de ahorro",
            "timestamp": timezone.now() - timedelta(days=1),
            "read": True,
            "category": "Metas",
            "action": "Ver meta",
        },
    ]
    # Añade el campo relative_time para la plantilla
    for n in notifications:
        n["relative_time"] = get_relative_time(n["timestamp"])
        n["hour"] = n["timestamp"].strftime("%H:%M")

    return render(request, "index.html", {
        "notifications": notifications
    })

def alertas_automaticas(request):
    """Vista para la configuración de alertas automáticas"""
    return render(request, "alertas_notificaciones/alertas_automaticas.html")

def historial(request):
    """Vista para el historial de notificaciones"""
    return render(request, "alertas_notificaciones/historial.html")

def configuraciones(request):
    """Vista para la configuración de notificaciones"""
    return render(request, "alertas_notificaciones/configuraciones.html")