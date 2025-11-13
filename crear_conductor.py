import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto2023.settings')
django.setup()

from core.models import Usuario

# Verificar si existe el conductor
conductor_existente = Usuario.objects.filter(username='conductor').first()

if conductor_existente:
    print(f"✓ El usuario conductor ya existe con ID {conductor_existente.id}")
    print(f"  - Email: {conductor_existente.email}")
    print(f"  - Role: {conductor_existente.role}")
    print(f"  - Nombre: {conductor_existente.first_name} {conductor_existente.last_name}")
else:
    # Crear el usuario conductor
    conductor = Usuario.objects.create_user(
        username='conductor',
        password='123456',
        email='conductor@ecopuntos.com',
        first_name='Conductor',
        last_name='',
        role='conductor',
        telefono='3001234567',
        direccion='Calle Principal 123'
    )
    print("✅ Usuario conductor creado exitosamente!")
    print(f"   - Username: conductor")
    print(f"   - Password: 123456")
    print(f"   - Email: {conductor.email}")
    print(f"   - Role: {conductor.role}")
    print(f"   - ID: {conductor.id}")

# Verificar todos los usuarios con role conductor
conductores = Usuario.objects.filter(role='conductor')
print(f"\n📋 Total de conductores en la base de datos: {conductores.count()}")
for c in conductores:
    print(f"   - {c.username} (ID: {c.id}) - {c.first_name} {c.last_name}")
