from django.core.management.base import BaseCommand
from core.security import SecurityManager
from django.utils import timezone

class Command(BaseCommand):
    help = 'Limpia sesiones expiradas e inactivas del sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra información detallada del proceso',
        )
    
    def handle(self, *args, **options):
        verbose = options['verbose']
        
        if verbose:
            self.stdout.write(f'Iniciando limpieza de sesiones - {timezone.now()}')
        
        # Limpiar sesiones expiradas
        expired_count = SecurityManager.cleanup_expired_sessions()
        
        # Limpiar sesiones inactivas
        inactive_count = SecurityManager.cleanup_inactive_sessions()
        
        total_cleaned = expired_count + inactive_count
        
        if verbose:
            self.stdout.write(f'Sesiones expiradas limpiadas: {expired_count}')
            self.stdout.write(f'Sesiones inactivas limpiadas: {inactive_count}')
            self.stdout.write(f'Total de sesiones limpiadas: {total_cleaned}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Limpieza completada exitosamente. {total_cleaned} sesiones eliminadas.'
            )
        )