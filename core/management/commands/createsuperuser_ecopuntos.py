from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
import getpass

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea un superusuario con privilegios máximos en el sistema EcoPuntos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            dest='username',
            help='Nombre de usuario para el superusuario',
        )
        parser.add_argument(
            '--email',
            dest='email',
            help='Email para el superusuario',
        )
        parser.add_argument(
            '--password',
            dest='password',
            help='Contraseña para el superusuario (no recomendado en producción)',
        )
        parser.add_argument(
            '--noinput',
            action='store_true',
            dest='interactive',
            help='No solicitar entrada interactiva del usuario',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        interactive = not options['interactive']

        # Modo interactivo
        if interactive:
            self.stdout.write(self.style.SUCCESS('\n=== CREACIÓN DE SUPERUSUARIO ECOPUNTOS ===\n'))
            
            # Solicitar username
            while not username:
                username = input('Nombre de usuario: ').strip()
                if not username:
                    self.stdout.write(self.style.ERROR('El nombre de usuario es requerido.'))
                elif User.objects.filter(username=username).exists():
                    self.stdout.write(self.style.ERROR(f'El usuario "{username}" ya existe.'))
                    username = None

            # Solicitar email
            while not email:
                email = input('Email: ').strip()
                if not email:
                    self.stdout.write(self.style.ERROR('El email es requerido.'))
                else:
                    try:
                        validate_email(email)
                        if User.objects.filter(email=email).exists():
                            self.stdout.write(self.style.ERROR(f'El email "{email}" ya está registrado.'))
                            email = None
                    except ValidationError:
                        self.stdout.write(self.style.ERROR('Email inválido.'))
                        email = None

            # Solicitar contraseña
            while not password:
                password = getpass.getpass('Contraseña: ')
                if len(password) < 8:
                    self.stdout.write(self.style.ERROR('La contraseña debe tener al menos 8 caracteres.'))
                    password = None
                else:
                    password_confirm = getpass.getpass('Confirmar contraseña: ')
                    if password != password_confirm:
                        self.stdout.write(self.style.ERROR('Las contraseñas no coinciden.'))
                        password = None

        else:
            # Modo no interactivo - validar que se proporcionaron todos los datos
            if not all([username, email, password]):
                raise CommandError('En modo no interactivo, username, email y password son requeridos.')

        # Validaciones finales
        if User.objects.filter(username=username).exists():
            raise CommandError(f'El usuario "{username}" ya existe.')

        if User.objects.filter(email=email).exists():
            raise CommandError(f'El email "{email}" ya está registrado.')

        try:
            validate_email(email)
        except ValidationError:
            raise CommandError('Email inválido.')

        # Crear el superusuario
        try:
            with transaction.atomic():
                superuser = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role='superuser',
                    is_staff=True,
                    is_active=True,
                    first_name='Super',
                    last_name='Usuario'
                )

                # Crear notificación de bienvenida
                from core.models import Notificacion
                Notificacion.objects.create(
                    usuario=superuser,
                    titulo='¡Bienvenido Superusuario!',
                    mensaje='Tu cuenta de superusuario ha sido creada exitosamente. Tienes control total sobre el sistema EcoPuntos.',
                    tipo='sistema'
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✅ Superusuario "{username}" creado exitosamente!\n'
                        f'📧 Email: {email}\n'
                        f'🔑 Rol: Superusuario\n'
                        f'🎯 Privilegios: Control total del sistema\n'
                        f'\nPuedes acceder al panel de administración en /paneladmin/\n'
                    )
                )

                # Mostrar información adicional sobre las capacidades
                self.stdout.write(
                    self.style.WARNING(
                        '🛡️  CAPACIDADES DEL SUPERUSUARIO:\n'
                        '   • Gestión total de usuarios (crear, eliminar, modificar)\n'
                        '   • Asignación y revocación de roles de administrador\n'
                        '   • Control completo sobre configuración del sistema\n'
                        '   • Acceso a todas las funcionalidades administrativas\n'
                        '   • Capacidad para promover/degradar administradores\n'
                        '   • Gestión de sesiones y seguridad del sistema\n'
                    )
                )

        except Exception as e:
            raise CommandError(f'Error al crear el superusuario: {str(e)}')
