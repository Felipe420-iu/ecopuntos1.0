import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto2023.settings')
django.setup()

from core.models import Usuario

# Buscar usuario Rengifo
try:
    usuarios = Usuario.objects.filter(username__icontains='rengifo')
    
    if usuarios.exists():
        for user in usuarios:
            print(f"\n{'='*50}")
            print(f"Usuario: {user.username}")
            print(f"ID: {user.id}")
            print(f"Nombre: {user.first_name} {user.last_name}")
            print(f"Email: {user.email}")
            print(f"Puntos actuales: {user.puntos}")
            print(f"Rol: {user.role}")
            print(f"Activo: {user.is_active}")
            print(f"{'='*50}\n")
    else:
        print("No se encontró ningún usuario con 'rengifo' en el nombre")
        
    # Mostrar todos los usuarios para referencia
    print("\n--- Todos los usuarios ---")
    for user in Usuario.objects.all():
        print(f"{user.id} - {user.username} - {user.puntos} puntos")
        
except Exception as e:
    print(f"Error: {e}")
