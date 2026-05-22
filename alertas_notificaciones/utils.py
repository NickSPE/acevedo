from django.utils import timezone

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
