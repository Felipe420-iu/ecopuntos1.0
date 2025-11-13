from django.core.management.base import BaseCommand
from core.models import Categoria, Recompensa
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Poblar la base de datos con categorías y recompensas de ejemplo'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando población de recompensas...")
        self.stdout.write("="*50)
        
        # Crear categorías
        self.stdout.write("\n1. Creando categorías...")
        categories = self.create_categories()
        
        # Crear recompensas
        self.stdout.write("\n2. Creando recompensas...")
        self.create_rewards(categories)
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("¡Población de recompensas completada!"))
        self.stdout.write(f"Total de categorías: {Categoria.objects.count()}")
        self.stdout.write(f"Total de recompensas: {Recompensa.objects.count()}")
        self.stdout.write("\nPuedes acceder al admin en: http://127.0.0.1:8000/admin/")
        self.stdout.write("Y ver las recompensas en: http://127.0.0.1:8000/recompensas/")

    def create_categories(self):
        """Crear categorías para las recompensas"""
        categories = [
            {'nombre': 'Electrónicos', 'activa': True},
            {'nombre': 'Hogar y Jardín', 'activa': True},
            {'nombre': 'Deportes y Fitness', 'activa': True},
            {'nombre': 'Alimentación', 'activa': True},
            {'nombre': 'Belleza y Cuidado Personal', 'activa': True},
            {'nombre': 'Libros y Educación', 'activa': True},
        ]
        
        for cat_data in categories:
            categoria, created = Categoria.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults={'activa': cat_data['activa']}
            )
            if created:
                self.stdout.write(f"Categoría creada: {categoria.nombre}")
            else:
                self.stdout.write(f"Categoría ya existe: {categoria.nombre}")
        
        return Categoria.objects.all()

    def create_rewards(self, categories):
        """Crear recompensas de ejemplo"""
        # Obtener categorías
        electronicos = categories.filter(nombre='Electrónicos').first()
        hogar = categories.filter(nombre='Hogar y Jardín').first()
        deportes = categories.filter(nombre='Deportes y Fitness').first()
        alimentacion = categories.filter(nombre='Alimentación').first()
        belleza = categories.filter(nombre='Belleza y Cuidado Personal').first()
        libros = categories.filter(nombre='Libros y Educación').first()
        
        rewards = [
            {
                'nombre': 'Auriculares Bluetooth Premium',
                'descripcion': 'Auriculares inalámbricos de alta calidad con cancelación de ruido y batería de larga duración.',
                'puntos_requeridos': 2500,
                'stock': 15,
                'categoria': electronicos,
                'imagen': 'core/img/recompesas.jpg',
                'es_popular': True,
                'es_nuevo': False,
                'es_oferta': False,
            },
            {
                'nombre': 'Smartwatch Deportivo',
                'descripcion': 'Reloj inteligente resistente al agua con monitor de frecuencia cardíaca y GPS integrado.',
                'puntos_requeridos': 3500,
                'stock': 8,
                'categoria': electronicos,
                'imagen': 'core/img/recompesas1.jpg',
                'es_popular': True,
                'es_nuevo': True,
                'es_oferta': False,
            },
            {
                'nombre': 'Set de Plantas Purificadoras',
                'descripcion': 'Conjunto de 3 plantas ideales para purificar el aire del hogar de forma natural.',
                'puntos_requeridos': 800,
                'stock': 25,
                'categoria': hogar,
                'imagen': 'core/img/recompesas2.jpg',
                'es_popular': False,
                'es_nuevo': False,
                'es_oferta': True,
            },
            {
                'nombre': 'Botella Térmica Ecológica',
                'descripcion': 'Botella reutilizable de acero inoxidable que mantiene la temperatura por 12 horas.',
                'puntos_requeridos': 600,
                'stock': 50,
                'categoria': deportes,
                'imagen': 'core/img/recompesas3.jpg',
                'es_popular': True,
                'es_nuevo': False,
                'es_oferta': False,
            },
            {
                'nombre': 'Kit de Productos Orgánicos',
                'descripcion': 'Selección de productos de cuidado personal 100% naturales y libres de químicos.',
                'puntos_requeridos': 1200,
                'stock': 20,
                'categoria': belleza,
                'imagen': 'core/img/recompesas4.jpg',
                'es_popular': False,
                'es_nuevo': True,
                'es_oferta': False,
            },
            {
                'nombre': 'Voucher Supermercado Ecológico',
                'descripcion': 'Cupón de descuento para compras en supermercados con productos orgánicos y sostenibles.',
                'puntos_requeridos': 1500,
                'stock': 100,
                'categoria': alimentacion,
                'imagen': 'core/img/recompesas5.jpg',
                'es_popular': True,
                'es_nuevo': False,
                'es_oferta': True,
            },
            {
                'nombre': 'Cargador Solar Portátil',
                'descripcion': 'Cargador de energía solar para dispositivos móviles, perfecto para actividades al aire libre.',
                'puntos_requeridos': 1800,
                'stock': 12,
                'categoria': electronicos,
                'imagen': 'core/img/recompesas.jpg',
                'es_popular': False,
                'es_nuevo': True,
                'es_oferta': False,
            },
            {
                'nombre': 'Libro de Sostenibilidad',
                'descripcion': 'Guía completa sobre prácticas sostenibles y cuidado del medio ambiente.',
                'puntos_requeridos': 400,
                'stock': 30,
                'categoria': libros,
                'imagen': 'core/img/recompesas1.jpg',
                'es_popular': False,
                'es_nuevo': False,
                'es_oferta': False,
            },
            {
                'nombre': 'Yoga Mat Ecológico',
                'descripcion': 'Esterilla de yoga fabricada con materiales reciclados y biodegradables.',
                'puntos_requeridos': 900,
                'stock': 5,  # Stock bajo para mostrar la funcionalidad
                'categoria': deportes,
                'imagen': 'core/img/recompesas2.jpg',
                'es_popular': False,
                'es_nuevo': False,
                'es_oferta': True,
            },
            {
                'nombre': 'Maceta Inteligente',
                'descripcion': 'Maceta con sistema de riego automático y sensores de humedad para plantas.',
                'puntos_requeridos': 2200,
                'stock': 0,  # Sin stock para mostrar la funcionalidad
                'categoria': hogar,
                'imagen': 'core/img/recompesas3.jpg',
                'es_popular': True,
                'es_nuevo': True,
                'es_oferta': False,
            }
        ]
        
        for reward_data in rewards:
            # Calcular fecha de vencimiento (3 meses desde ahora)
            fecha_vencimiento = timezone.now().date() + timedelta(days=90)
            
            recompensa, created = Recompensa.objects.get_or_create(
                nombre=reward_data['nombre'],
                defaults={
                    'descripcion': reward_data['descripcion'],
                    'puntos_requeridos': reward_data['puntos_requeridos'],
                    'stock': reward_data['stock'],
                    'categoria': reward_data['categoria'],
                    'imagen': reward_data['imagen'],
                    'es_popular': reward_data['es_popular'],
                    'es_nuevo': reward_data['es_nuevo'],
                    'es_oferta': reward_data['es_oferta'],
                    'fecha_vencimiento': fecha_vencimiento,
                    'activa': True,
                    'veces_canjeada': 0
                }
            )
            
            if created:
                self.stdout.write(f"Recompensa creada: {recompensa.nombre} ({recompensa.puntos_requeridos} puntos)")
            else:
                self.stdout.write(f"Recompensa ya existe: {recompensa.nombre}")