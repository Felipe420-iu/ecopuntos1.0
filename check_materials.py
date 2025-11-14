import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto2023.settings')
django.setup()

from core.models import MaterialTasa

# Mostrar todos los materiales
materiales = MaterialTasa.objects.all()

print("Materiales configurados:")
print("="*60)
for material in materiales:
    print(f"ID: {material.id}")
    print(f"Nombre: {material.nombre}")
    print(f"Puntos por kilo: {material.puntos_por_kilo}")
    print(f"Activo: {material.activo}")
    print(f"Descripción: {material.descripcion}")
    print("-"*60)
