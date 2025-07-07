# core/management/commands/clear_sessions.py
from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Limpia sesiones expiradas o todas las sesiones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Eliminar TODAS las sesiones (forzar logout a todos los usuarios)',
        )
        parser.add_argument(
            '--expired',
            action='store_true',
            help='Eliminar solo sesiones expiradas (por defecto)',
        )

    def handle(self, *args, **options):
        if options['all']:
            # Eliminar todas las sesiones
            count_before = Session.objects.count()
            Session.objects.all().delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Eliminadas TODAS las sesiones ({count_before} sesiones)'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Todos los usuarios han sido desconectados'
                )
            )
            
        else:
            # Eliminar solo sesiones expiradas (comportamiento por defecto)
            count_before = Session.objects.count()
            
            # Eliminar sesiones expiradas
            expired_sessions = Session.objects.filter(
                expire_date__lt=timezone.now()
            )
            expired_count = expired_sessions.count()
            expired_sessions.delete()
            
            count_after = Session.objects.count()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Sesiones limpiadas:'
                )
            )
            self.stdout.write(f'   📊 Antes: {count_before} sesiones')
            self.stdout.write(f'   🗑️  Expiradas eliminadas: {expired_count}')
            self.stdout.write(f'   📊 Después: {count_after} sesiones')
            
            if expired_count == 0:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️  No había sesiones expiradas para eliminar'
                    )
                )
