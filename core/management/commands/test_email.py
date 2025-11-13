"""
Comando para probar el sistema de notificaciones por email
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Canje, MaterialTasa
from core.notifications import NotificacionEmail

User = get_user_model()

class Command(BaseCommand):
    help = 'Prueba el sistema de notificaciones por email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email del usuario para enviar la prueba',
        )
        parser.add_argument(
            '--tipo',
            type=str,
            choices=['bienvenida', 'canje_solicitado', 'canje_aprobado', 'canje_revision'],
            default='bienvenida',
            help='Tipo de notificación a probar',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        tipo = options.get('tipo')

        if not email:
            self.stdout.write(
                self.style.ERROR('Debes proporcionar un email con --email tu@email.com')
            )
            return

        # Buscar o crear usuario de prueba
        try:
            usuario = User.objects.get(email=email)
            self.stdout.write(f"Usuario encontrado: {usuario.username}")
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'No se encontró usuario con email {email}')
            )
            return

        # Verificar que el usuario tenga notificaciones activadas
        if not usuario.notificaciones_email:
            self.stdout.write(
                self.style.WARNING('El usuario tiene las notificaciones por email desactivadas')
            )
            respuesta = input('¿Activar notificaciones temporalmente? (s/n): ')
            if respuesta.lower() == 's':
                usuario.notificaciones_email = True
                usuario.save()
                self.stdout.write('Notificaciones activadas temporalmente')
            else:
                return

        # Enviar notificación según el tipo
        self.stdout.write(f"Enviando notificación de tipo: {tipo}")

        try:
            if tipo == 'bienvenida':
                resultado = NotificacionEmail.notificar_bienvenida(usuario)
                
            elif tipo == 'canje_solicitado':
                # Crear un canje de prueba (sin guardar en BD)
                material = MaterialTasa.objects.first()
                if not material:
                    self.stdout.write(self.style.ERROR('No hay materiales en la base de datos'))
                    return
                
                canje = Canje(
                    id=999,
                    usuario=usuario,
                    material=material,
                    peso=5.0,
                    puntos=250,
                    estado='pendiente'
                )
                resultado = NotificacionEmail.notificar_canje_solicitado(canje)
                
            elif tipo == 'canje_aprobado':
                material = MaterialTasa.objects.first()
                if not material:
                    self.stdout.write(self.style.ERROR('No hay materiales en la base de datos'))
                    return
                
                canje = Canje(
                    id=999,
                    usuario=usuario,
                    material=material,
                    peso=5.0,
                    puntos=250,
                    estado='aprobado'
                )
                resultado = NotificacionEmail.notificar_canje_aprobado(canje)
                
            elif tipo == 'canje_revision':
                material = MaterialTasa.objects.first()
                if not material:
                    self.stdout.write(self.style.ERROR('No hay materiales en la base de datos'))
                    return
                
                canje = Canje(
                    id=999,
                    usuario=usuario,
                    material=material,
                    peso=5.0,
                    puntos=250,
                    estado='en_revision'
                )
                resultado = NotificacionEmail.notificar_canje_en_revision(canje)

            if resultado:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Email enviado exitosamente a {email}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error enviando email a {email}')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )

        self.stdout.write("\n" + "="*50)
        self.stdout.write("CONFIGURACIÓN ACTUAL:")
        self.stdout.write("="*50)
        
        from django.conf import settings
        self.stdout.write(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'No configurado')}")
        self.stdout.write(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'No configurado')}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado')}")
        
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            self.stdout.write(
                self.style.WARNING('\n⚠️ Usando console backend - los emails aparecerán en la consola')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✅ Usando SMTP backend - los emails se enviarán realmente')
            )
