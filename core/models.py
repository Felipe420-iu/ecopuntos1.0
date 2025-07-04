from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('user', 'Usuario Regular'),
    )
    role = models.CharField(max_length=10, choices=ROLES, default='user')
    puntos = models.IntegerField(default=0)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.username

    def is_admin_user(self):
        return self.role == 'admin'

class MaterialTasa(models.Model):
    nombre = models.CharField(max_length=100)
    puntos_por_kilo = models.IntegerField()
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.nombre} - {self.puntos_por_kilo} puntos/kg'

class Canje(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('completado', 'Completado')
    )
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    material = models.ForeignKey(MaterialTasa, on_delete=models.PROTECT)
    peso = models.DecimalField(max_digits=10, decimal_places=2)
    puntos = models.IntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True)
    comprobante = models.ImageField(upload_to='comprobantes/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.puntos:
            self.puntos = int(float(self.peso) * self.material.puntos_por_kilo)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Canje de {self.usuario.username} - {self.material.nombre}'

class RedencionPuntos(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('rechazado', 'Rechazado')
    )
    
    METODOS_PAGO = (
        ('nequi', 'Nequi'),
        ('daviplata', 'Daviplata'),
        ('bancolombia', 'Bancolombia')
    )
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    puntos = models.IntegerField()
    valor_cop = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO)
    numero_cuenta = models.CharField(max_length=50)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    notas_admin = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.valor_cop:
            # Tasa de conversión: 1 punto = 0.5 COP
            self.valor_cop = self.puntos * 0.5
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Redención de {self.usuario.username} - {self.puntos} puntos'

class Ruta(models.Model):
    fecha = models.DateField()
    hora = models.TimeField()
    barrio = models.CharField(max_length=100)
    referencia = models.TextField(blank=True, null=True)
    direccion = models.CharField(max_length=255)

    def __str__(self):
        return f'Ruta el {self.fecha} a las {self.hora} en {self.barrio}'

class Alerta(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Configuracion(models.Model):
    CATEGORIAS = [
        ('puntos', 'Configuración de Puntos'),
        ('rutas', 'Configuración de Rutas'),
        ('materiales', 'Configuración de Materiales'),
        ('notificaciones', 'Configuración de Notificaciones'),
        ('general', 'Configuración General'),
    ]
    
    nombre = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='general')
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    TIPOS_CONFIG = [
        ('texto', 'Texto'),
        ('numero', 'Número'),
        ('booleano', 'Booleano'),
        ('json', 'JSON'),
        ('lista', 'Lista'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPOS_CONFIG, default='texto')
    
    def __str__(self):
        return f"{self.nombre} ({self.get_categoria_display()})"
    
    class Meta:
        verbose_name = 'Configuración'
        verbose_name_plural = 'Configuraciones'
        ordering = ['categoria', 'nombre']

    @classmethod
    def get_configs_by_category(cls, categoria):
        return cls.objects.filter(categoria=categoria)

class Recompensa(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    puntos_requeridos = models.IntegerField()
    stock = models.IntegerField(default=0)
    activa = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='recompensas/', null=True, blank=True)
    # Assuming categories for rewards as well, if needed.
    # categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre

class Logro(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=50)  # Ejemplo: 'nivel', 'canje', 'evento'
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    puntos = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Logro'
        verbose_name_plural = 'Logros'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.usuario.username} - {self.descripcion}'

# Create your models here.
