import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto2023.settings')
django.setup()

from core.models import Usuario, Notificacion

# Buscar usuario Rengifo
try:
    user = Usuario.objects.get(username='Rengifo')
    
    print(f"\nUsuario: {user.username}")
    print(f"Puntos antes: {user.puntos}")
    
    # Añadir 50 puntos
    cantidad = 50
    user.puntos += cantidad
    user.save()
    
    print(f"Puntos después de añadir {cantidad}: {user.puntos}")
    
    # Crear notificación
    Notificacion.objects.create(
        usuario=user,
        tipo='puntos',
        mensaje=f'Un administrador ha añadido {cantidad} puntos a tu cuenta. (Prueba manual)'
    )
    
    print(f"\n✅ Actualización exitosa!")
    print(f"Total de puntos ahora: {user.puntos}")
    
except Usuario.DoesNotExist:
    print("❌ No se encontró el usuario Rengifo")
except Exception as e:
    print(f"❌ Error: {e}")
