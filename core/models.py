from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.conf import settings
from django.utils import timezone

class Configuracion(models.Model):
    CATEGORIAS = (
        ('general', 'General'),
        ('sesiones', 'Sesiones'),
        ('seguridad', 'Seguridad'),
    )

    categoria = models.CharField(max_length=50, choices=CATEGORIAS, default='general')
    nombre = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración'
        verbose_name_plural = 'Configuraciones'
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return f"{self.categoria} - {self.nombre}"

    @classmethod
    def get_configs_by_category(cls, categoria):
        return cls.objects.filter(categoria=categoria)

class Usuario(AbstractUser):
    ROLES = (
        ('superuser', 'Superusuario'),
        ('admin', 'Administrador'),
        ('conductor', 'Conductor'),
        ('user', 'Usuario Regular'),
    )
    
    LEVELS = (
        ('guardian_verde', 'Guardián Verde'),
        ('defensor_planeta', 'Defensor del Planeta'),
        ('heroe_eco', 'Héroe Eco'),
        ('embajador_ambiental', 'Embajador Ambiental'),
        ('leyenda_sustentable', 'Leyenda Sustentable'),
    )
    
    role = models.CharField(max_length=10, choices=ROLES, default='user')
    level = models.CharField(max_length=25, choices=LEVELS, default='guardian_verde')
    puntos = models.IntegerField(default=0)
    puntos_juego = models.IntegerField(default=0)  # Puntos acumulados en juegos de plásticos
    puntos_juego_vidrios = models.IntegerField(default=0)  # Puntos acumulados en juegos de vidrios
    puntos_juego_papel = models.IntegerField(default=0)  # Puntos acumulados en el juego de papel y cartón
    puntos_juego_metales = models.IntegerField(default=0)  # Puntos acumulados en el juego de metales
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)
    testimonio = models.TextField("Testimonio", blank=True, null=True)
    notificaciones_email = models.BooleanField(default=True)
    notificaciones_push = models.BooleanField(default=False)
    perfil_publico = models.BooleanField(default=True)
    mostrar_puntos = models.BooleanField(default=True)
    foto_perfil = models.ImageField(upload_to='fotos_perfil/', null=True, blank=True)
    suspended = models.BooleanField(default=False, help_text="Usuario suspendido permanentemente")
    terminos_aceptados = models.BooleanField(default=False, help_text="Usuario ha aceptado los términos y condiciones")
    fecha_aceptacion_terminos = models.DateTimeField(null=True, blank=True, help_text="Fecha cuando aceptó los términos")
    
    # Campos para 2FA por email
    email_verificado = models.BooleanField(default=False, help_text="Email verificado con código 2FA")
    codigo_verificacion = models.CharField(max_length=6, blank=True, null=True, help_text="Código de verificación 2FA")
    codigo_verificacion_expira = models.DateTimeField(null=True, blank=True, help_text="Expiración del código 2FA")
    intentos_verificacion = models.IntegerField(default=0, help_text="Intentos fallidos de verificación")
    verificacion_bloqueada_hasta = models.DateTimeField(null=True, blank=True, help_text="Bloqueo temporal por intentos fallidos")
    
    # Configurar email como único
    email = models.EmailField(unique=True)
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.username

    def is_admin_user(self):
        return self.role == 'admin'
    
    def is_conductor(self):
        return self.role == 'conductor'
    
    def is_superuser_role(self):
        return self.role == 'superuser'
    
    def is_elevated_user(self):
        """Verifica si el usuario tiene permisos elevados (admin, conductor o superuser)"""
        return self.role in ['admin', 'superuser', 'conductor']
    
    def get_initials(self):
        """Obtiene las iniciales del usuario"""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return self.first_name[0].upper()
        else:
            return self.username[0].upper() if self.username else "U"
    
    def get_avatar_color(self):
        """Genera un color único basado en el ID del usuario"""
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
            '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2'
        ]
        return colors[self.id % len(colors)]
    
    def get_avatar_svg(self):
        """Genera un avatar SVG único para el usuario"""
        initials = self.get_initials()
        color = self.get_avatar_color()
        return f'''
        <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="50" fill="{color}"/>
            <text x="50" y="50" font-family="Arial, sans-serif" font-size="36" font-weight="bold" 
                  fill="white" text-anchor="middle" dominant-baseline="central">{initials}</text>
        </svg>
        '''

    @classmethod
    def usuarios_con_testimonio(cls):
        return cls.objects.filter(testimonio__isnull=False).exclude(testimonio="").filter(is_active=True)

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
        ('confirmado', 'Confirmado'),
        ('recolectado', 'Recolectado'),
        ('verificando', 'Verificando'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('completado', 'Completado'),
        ('pendiente_recoleccion', 'Pendiente Recolección'),  # Para canjes con recolección
        ('en_recoleccion', 'En Recolección'),  # Cuando están siendo recolectados
    )
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    material = models.ForeignKey(MaterialTasa, on_delete=models.PROTECT)
    peso = models.DecimalField(max_digits=10, decimal_places=2)
    peso_real = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Campo de migración 0032
    puntos = models.IntegerField()
    puntos_finales = models.IntegerField(null=True, blank=True)  # Campo de migración 0032
    estado = models.CharField(max_length=25, choices=ESTADOS, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True)
    comprobante = models.ImageField(upload_to='comprobantes/', null=True, blank=True)
    
    # Campos para integración con rutas (de migración 0032)
    necesita_recoleccion = models.BooleanField(default=True)  # Campo de migración 0032
    direccion_recoleccion = models.CharField(max_length=255, blank=True)  # Campo de migración 0032
    telefono_contacto = models.CharField(max_length=20, blank=True)  # Campo de migración 0032
    horario_disponible = models.CharField(max_length=100, blank=True)  # Campo de migración 0032
    referencia_direccion = models.TextField(blank=True)  # Campo de migración 0032
    foto_material_inicial = models.ImageField(upload_to='materiales_iniciales/', null=True, blank=True)  # Campo de migración 0032
    foto_material_recolectado = models.ImageField(upload_to='materiales_recolectados/', null=True, blank=True)  # Campo de migración 0032
    ruta_asignada = models.ForeignKey('RutaRecoleccion', on_delete=models.SET_NULL, null=True, blank=True)  # Campo de migración 0032

    def save(self, *args, **kwargs):
        if not self.puntos:
            self.puntos = int(float(self.peso) * self.material.puntos_por_kilo)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Canje de {self.usuario.username} - {self.material.nombre}'

class RedencionPuntos(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
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
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('rechazada', 'Rechazada'),
        ('reagendada', 'Reagendada'),
        ('completada', 'Completada')
    )
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rutas', null=True, blank=True)
    fecha = models.DateField()
    hora = models.TimeField()
    barrio = models.CharField(max_length=100)
    referencia = models.TextField(blank=True, null=True)
    direccion = models.CharField(max_length=255)
    materiales = models.CharField(max_length=255, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    notas_admin = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Ruta el {self.fecha} a las {self.hora} en {self.barrio} - {self.get_estado_display()}'

class RutaRecoleccion(models.Model):
    """Modelo principal para la gestión de rutas de recolección integradas con canjes"""
    
    ESTADOS = (
        ('planificada', 'Planificada'),
        ('programada', 'Programada'),  
        ('en_curso', 'En Curso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada')
    )
    
    TIPOS_VEHICULO = (
        ('moto', 'Motocicleta'),
        ('camion_pequeno', 'Camión Pequeño'),
        ('camion_grande', 'Camión Grande')
    )
    
    # Información básica de la ruta
    nombre = models.CharField(max_length=100)  # Ej: "Ruta Norte - Día 1"
    fecha_programada = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin_estimada = models.TimeField()
    zona = models.CharField(max_length=50)  # Norte, Sur, Este, Oeste, Centro
    
    # Asignación de recursos
    conductor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='rutas_conductor')
    vehiculo_tipo = models.CharField(max_length=20, choices=TIPOS_VEHICULO, default='camion_pequeno')
    capacidad_maxima = models.DecimalField(max_digits=8, decimal_places=2, default=100.0)  # kg
    
    # Estado y seguimiento
    estado = models.CharField(max_length=20, choices=ESTADOS, default='planificada')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio_real = models.DateTimeField(null=True, blank=True)
    fecha_fin_real = models.DateTimeField(null=True, blank=True)
    
    # Información adicional
    notas = models.TextField(blank=True)
    kilometros_recorridos = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    costo_combustible = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f'{self.nombre} - {self.fecha_programada} ({self.get_estado_display()})'
    
    @property
    def canjes_asignados(self):
        """Retorna todos los canjes asignados a esta ruta"""
        return self.canje_set.all()
    
    @property
    def peso_total_estimado(self):
        """Calcula el peso total estimado de todos los canjes"""
        return sum(canje.peso for canje in self.canjes_asignados)
    
    @property
    def peso_total_real(self):
        """Calcula el peso total real de todos los canjes recolectados"""
        return sum(canje.peso_real or 0 for canje in self.canjes_asignados if canje.peso_real)
    
    @property
    def total_puntos_estimados(self):
        """Calcula el total de puntos estimados"""
        return sum(canje.puntos for canje in self.canjes_asignados)
    
    @property
    def total_usuarios(self):
        """Número de usuarios únicos en esta ruta"""
        return self.canjes_asignados.values('usuario').distinct().count()
    
    @property
    def paradas_completadas(self):
        """Número de paradas completadas"""
        return self.canjes_asignados.filter(estado='recolectado').count()
    
    @property
    def paradas_totales(self):
        """Número total de paradas"""
        return self.canjes_asignados.count()
    
    @property
    def progreso_porcentaje(self):
        """Porcentaje de progreso de la ruta"""
        if self.paradas_totales == 0:
            return 0
        return (self.paradas_completadas / self.paradas_totales) * 100

class ParadaRuta(models.Model):
    """Modelo para gestionar cada parada individual dentro de una ruta"""
    
    ESTADOS_PARADA = (
        ('pendiente', 'Pendiente'),
        ('en_camino', 'En Camino'),
        ('llegada', 'Llegada'),
        ('recolectando', 'Recolectando'),
        ('completada', 'Completada'),
        ('no_encontrado', 'No Encontrado'),
        ('reagendada', 'Reagendada')
    )
    
    ruta = models.ForeignKey(RutaRecoleccion, on_delete=models.CASCADE, related_name='paradas')
    canje = models.OneToOneField(Canje, on_delete=models.CASCADE, related_name='parada')
    orden = models.PositiveIntegerField()  # Orden de visita en la ruta
    
    # Información de la parada
    direccion = models.CharField(max_length=255)
    referencia = models.TextField(blank=True)
    telefono_contacto = models.CharField(max_length=20)
    horario_preferido = models.CharField(max_length=100, blank=True)
    
    # Estado y timing
    estado = models.CharField(max_length=20, choices=ESTADOS_PARADA, default='pendiente')
    hora_llegada_estimada = models.TimeField(null=True, blank=True)
    hora_llegada_real = models.DateTimeField(null=True, blank=True)
    hora_salida_real = models.DateTimeField(null=True, blank=True)
    
    # Información de recolección
    peso_recolectado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    observaciones = models.TextField(blank=True)
    foto_antes = models.ImageField(upload_to='paradas/antes/', null=True, blank=True)
    foto_despues = models.ImageField(upload_to='paradas/despues/', null=True, blank=True)
    
    class Meta:
        ordering = ['orden']
        unique_together = ['ruta', 'orden']
    
    def __str__(self):
        return f'Parada {self.orden} - {self.canje.usuario.username} ({self.get_estado_display()})'

class Alerta(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Recompensa(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    puntos_requeridos = models.IntegerField()
    stock = models.IntegerField(default=0)
    activa = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='recompensas/', null=True, blank=True)
    categoria = models.ForeignKey('Categoria', on_delete=models.SET_NULL, null=True, blank=True)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    es_popular = models.BooleanField(default=False)
    es_nuevo = models.BooleanField(default=False)
    es_oferta = models.BooleanField(default=False)
    veces_canjeada = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    @property
    def stock_bajo(self):
        return self.stock <= 5 and self.stock > 0
    
    @property
    def sin_stock(self):
        return self.stock <= 0

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

class FavoritoRecompensa(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    recompensa = models.ForeignKey(Recompensa, on_delete=models.CASCADE)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('usuario', 'recompensa')
        verbose_name = 'Favorito Recompensa'
        verbose_name_plural = 'Favoritos Recompensas'
    
    def __str__(self):
        return f'{self.usuario.username} - {self.recompensa.nombre}'

class Notificacion(models.Model):
    TIPOS_NOTIFICACION = [
        ('canje_pendiente', 'Canje Pendiente'),
        ('canje_aprobado', 'Canje Aprobado'),
        ('canje_rechazado', 'Canje Rechazado'),
        ('redencion_pendiente', 'Redención Pendiente'),
        ('redencion_aprobada', 'Redención Aprobada'),
        ('redencion_rechazada', 'Redención Rechazada'),
        ('recompensa_canjeada', 'Recompensa Canjeada'),
        ('retiro_enviado', 'Retiro Enviado'),
        ('perfil_actualizado', 'Perfil Actualizado'),
        ('password_cambiado', 'Contraseña Cambiada'),
        ('foto_actualizada', 'Foto Actualizada'),
        ('sistema', 'Sistema'),
    ]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    titulo = models.CharField(max_length=200, default='Notificación')
    mensaje = models.TextField()
    tipo = models.CharField(max_length=30, choices=TIPOS_NOTIFICACION, default='sistema')
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        return f"Notificación para {self.usuario.username}: {self.mensaje[:30]}..."

class SesionUsuario(models.Model):
    """Modelo para manejar sesiones seguras con validación de dispositivos"""
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='sesiones')
    token_sesion = models.CharField(max_length=255, unique=True)
    dispositivo_id = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    activa = models.BooleanField(default=True)
    ultima_actividad = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Sesión de Usuario'
        verbose_name_plural = 'Sesiones de Usuario'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Sesión de {self.usuario.username} - {self.dispositivo_id}"
    
    def is_expired(self):
        return timezone.now() > self.fecha_expiracion
    
    def is_valid(self):
        return self.activa and not self.is_expired()

class IntentoAcceso(models.Model):
    """Modelo para registrar intentos de acceso no autorizado"""
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    url_intento = models.URLField()
    fecha_intento = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=100)  # 'token_invalido', 'sesion_expirada', 'dispositivo_no_autorizado'
    
    class Meta:
        verbose_name = 'Intento de Acceso'
        verbose_name_plural = 'Intentos de Acceso'
        ordering = ['-fecha_intento']
    
    def __str__(self):
        return f"Intento desde {self.ip_address} - {self.motivo}"



class MovimientoStock(models.Model):
    """Modelo para registrar movimientos de stock de recompensas"""
    TIPOS_MOVIMIENTO = [
        ('canje', 'Canje de Usuario'),
        ('ajuste_manual', 'Ajuste Manual'),
        ('reabastecimiento', 'Reabastecimiento'),
        ('correccion', 'Corrección'),
        ('devolucion', 'Devolución'),
    ]
    
    recompensa = models.ForeignKey(Recompensa, on_delete=models.CASCADE, related_name='movimientos_stock')
    tipo_movimiento = models.CharField(max_length=20, choices=TIPOS_MOVIMIENTO)
    cantidad_anterior = models.IntegerField()
    cantidad_nueva = models.IntegerField()
    cantidad_cambiada = models.IntegerField()  # Puede ser positiva o negativa
    motivo = models.TextField(blank=True)
    usuario_responsable = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    canje_relacionado = models.ForeignKey('Canje', on_delete=models.SET_NULL, null=True, blank=True)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Movimiento de Stock'
        verbose_name_plural = 'Movimientos de Stock'
        ordering = ['-fecha_movimiento']
    
    def __str__(self):
        return f"{self.recompensa.nombre} - {self.get_tipo_movimiento_display()} ({self.cantidad_cambiada:+d})"

class SeguimientoRecompensa(models.Model):
    """Modelo para el seguimiento de recompensas físicas canjeadas"""
    
    ESTADOS_SEGUIMIENTO = (
        ('solicitado', 'Solicitado'),
        ('confirmado', 'Confirmado'),
        ('preparando', 'Preparando Pedido'),
        ('empacado', 'Empacado'),
        ('en_transito', 'En Tránsito'),
        ('en_reparto', 'En Reparto'),
        ('entregado', 'Entregado'),
        ('problema', 'Problema en Entrega'),
        ('cancelado', 'Cancelado')
    )
    
    # Relaciones
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='seguimientos_recompensa')
    recompensa = models.ForeignKey(Recompensa, on_delete=models.CASCADE, related_name='seguimientos')
    redencion = models.OneToOneField(RedencionPuntos, on_delete=models.CASCADE, related_name='seguimiento', null=True, blank=True)
    
    # Información del pedido
    codigo_seguimiento = models.CharField(max_length=20, unique=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_SEGUIMIENTO, default='solicitado')
    
    # Información de entrega
    direccion_entrega = models.TextField()
    telefono_contacto = models.CharField(max_length=20)
    fecha_estimada_entrega = models.DateTimeField(null=True, blank=True)
    fecha_entrega_real = models.DateTimeField(null=True, blank=True)
    
    # Información adicional
    notas_adicionales = models.TextField(blank=True)
    foto_entrega = models.ImageField(upload_to='entregas/', null=True, blank=True)
    calificacion_servicio = models.IntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    
    # Timestamps
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Seguimiento de Recompensa'
        verbose_name_plural = 'Seguimientos de Recompensas'
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"{self.codigo_seguimiento} - {self.recompensa.nombre} ({self.get_estado_display()})"
    
    def save(self, *args, **kwargs):
        if not self.codigo_seguimiento:
            import random
            import string
            self.codigo_seguimiento = 'EP' + ''.join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)
    
    @property
    def porcentaje_progreso(self):
        """Calcula el porcentaje de progreso basado en el estado"""
        estados_orden = [estado[0] for estado in self.ESTADOS_SEGUIMIENTO if estado[0] not in ['problema', 'cancelado']]
        if self.estado in ['problema', 'cancelado']:
            return 0
        try:
            indice = estados_orden.index(self.estado)
            return int((indice + 1) / len(estados_orden) * 100)
        except ValueError:
            return 0
    
    @property
    def estado_color(self):
        """Retorna el color del estado para la UI"""
        colores = {
            'solicitado': '#6c757d',
            'confirmado': '#0dcaf0',
            'preparando': '#fd7e14',
            'empacado': '#ffc107',
            'en_transito': '#20c997',
            'en_reparto': '#0d6efd',
            'entregado': '#198754',
            'problema': '#dc3545',
            'cancelado': '#6c757d'
        }
        return colores.get(self.estado, '#6c757d')

class HistorialSeguimiento(models.Model):
    """Historial de cambios de estado en el seguimiento"""
    
    seguimiento = models.ForeignKey(SeguimientoRecompensa, on_delete=models.CASCADE, related_name='historial')
    estado_anterior = models.CharField(max_length=20, choices=SeguimientoRecompensa.ESTADOS_SEGUIMIENTO, null=True, blank=True)
    estado_nuevo = models.CharField(max_length=20, choices=SeguimientoRecompensa.ESTADOS_SEGUIMIENTO)
    comentario = models.TextField(blank=True)
    usuario_responsable = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    ubicacion = models.CharField(max_length=200, blank=True)
    
    class Meta:
        verbose_name = 'Historial de Seguimiento'
        verbose_name_plural = 'Historiales de Seguimiento'
        ordering = ['-fecha_cambio']
    
    def __str__(self):
        return f"{self.seguimiento.codigo_seguimiento} - {self.get_estado_nuevo_display()}"

# ====================================
# MODELOS DEL CHATBOT IA
# ====================================

class ConversacionChatbot(models.Model):
    """Conversación entre usuario y chatbot IA"""
    
    ESTADOS = [
        ('activa', 'Activa'),
        ('finalizada', 'Finalizada'),
        ('escalada', 'Escalada a Humano'),
        ('pausada', 'Pausada'),
    ]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='conversaciones_chatbot')
    session_id = models.CharField(max_length=100, unique=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activa')
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    escalado_a_humano = models.BooleanField(default=False)
    
    # Metadatos de la conversación
    total_mensajes = models.IntegerField(default=0)
    promedio_confianza = models.FloatField(null=True, blank=True)
    temas_identificados = models.JSONField(default=list, blank=True)
    
    class Meta:
        verbose_name = 'Conversación Chatbot'
        verbose_name_plural = 'Conversaciones Chatbot'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"Conversación {self.session_id} - {self.usuario.username}"
    
    def finalizar(self):
        """Finaliza la conversación"""
        self.estado = 'finalizada'
        self.fecha_fin = timezone.now()
        self.save()
    
    def escalar_a_humano(self, motivo="Solicitud de usuario"):
        """Escala la conversación a un humano - Funcionalidad completa"""
        if not self.escalado_a_humano:
            # Crear solicitud de soporte en la base de datos
            try:
                # Importar el modelo SolicitudSoporte para evitar importaciones circulares
                from core.models import SolicitudSoporte
                
                # Crear la solicitud de soporte
                solicitud = SolicitudSoporte.objects.create(
                    usuario=self.usuario,
                    estado='pendiente',
                    mensaje=motivo
                )
                
                print(f"✅ Solicitud de soporte creada con ID: {solicitud.id}")
                
            except Exception as e:
                print(f"❌ Error creando solicitud de soporte: {e}")
            
            # Enviar notificación por email
            from django.core.mail import send_mail
            from django.conf import settings
            
            try:
                send_mail(
                    subject=f'Solicitud de soporte de {self.usuario.username}',
                    message=f'El usuario {self.usuario.get_full_name() or self.usuario.username} ha solicitado hablar con un agente humano.\n\nMotivo: {motivo}\n\nConversación ID: {self.session_id}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=['soporte@ecopuntos.com'],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Error enviando email de escalamiento: {e}")
            
            self.escalado_a_humano = True
            self.estado = 'escalada'
            self.save()
            
            # Crear notificación para el usuario
            from .models import Notificacion
            Notificacion.objects.create(
                usuario=self.usuario,
                titulo='Solicitud de soporte enviada',
                mensaje='Tu solicitud ha sido enviada al equipo de soporte. Te contactaremos pronto por email.',
                tipo='sistema'
            )
            
            return True
        
        return False

class MensajeChatbot(models.Model):
    """Mensaje individual en una conversación con el chatbot"""
    
    conversacion = models.ForeignKey(ConversacionChatbot, on_delete=models.CASCADE, related_name='mensajes')
    contenido = models.TextField()
    es_usuario = models.BooleanField()  # True=usuario, False=IA
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Metadatos de IA
    confidence_score = models.FloatField(null=True, blank=True)  # Confianza de la respuesta (0-1)
    intent_detected = models.CharField(max_length=100, blank=True)  # Intención detectada
    entities_extracted = models.JSONField(default=dict, blank=True)  # Entidades extraídas
    response_time_ms = models.IntegerField(null=True, blank=True)  # Tiempo de respuesta en ms
    
    # Información del modelo de IA
    ai_model_used = models.CharField(max_length=50, blank=True)  # ej: gpt-3.5-turbo
    tokens_used = models.IntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Mensaje Chatbot'
        verbose_name_plural = 'Mensajes Chatbot'
        ordering = ['timestamp']
    
    def __str__(self):
        tipo = "Usuario" if self.es_usuario else "IA"
        return f"{tipo}: {self.contenido[:50]}..."

class ContextoChatbot(models.Model):
    """Contexto acumulado de una conversación para mejorar respuestas"""
    
    conversacion = models.OneToOneField(ConversacionChatbot, on_delete=models.CASCADE, related_name='contexto')
    
    # Información del usuario
    datos_usuario = models.JSONField(default=dict, blank=True)  # Preferencias, historial, etc.
    
    # Contexto de la conversación
    temas_discutidos = models.JSONField(default=list, blank=True)  # Lista de temas
    problemas_identificados = models.JSONField(default=list, blank=True)  # Problemas del usuario
    soluciones_propuestas = models.JSONField(default=list, blank=True)  # Soluciones ofrecidas
    
    # Estado emocional/satisfacción
    sentimiento_usuario = models.CharField(max_length=20, blank=True)  # positivo, negativo, neutral
    nivel_frustacion = models.IntegerField(default=0)  # 0-10
    satisfaccion_estimada = models.IntegerField(null=True, blank=True)  # 1-5
    
    # Flags de escalamiento
    requiere_escalamiento = models.BooleanField(default=False)
    motivo_escalamiento = models.CharField(max_length=200, blank=True)
    
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Contexto Chatbot'
        verbose_name_plural = 'Contextos Chatbot'
    
    def __str__(self):
        return f"Contexto - {self.conversacion.session_id}"
    
    def actualizar_sentimiento(self, mensaje_texto):
        """Actualiza el sentimiento basado en el último mensaje del usuario"""
        # Aquí se podría integrar análisis de sentimientos
        # Por ahora, detección básica de palabras clave
        palabras_negativas = ['molesto', 'frustrado', 'enojado', 'mal', 'problema', 'error']
        palabras_positivas = ['gracias', 'excelente', 'genial', 'perfecto', 'bien']
        
        texto_lower = mensaje_texto.lower()
        
        if any(palabra in texto_lower for palabra in palabras_negativas):
            self.sentimiento_usuario = 'negativo'
            self.nivel_frustacion = min(self.nivel_frustacion + 1, 10)
        elif any(palabra in texto_lower for palabra in palabras_positivas):
            self.sentimiento_usuario = 'positivo'
            self.nivel_frustacion = max(self.nivel_frustacion - 1, 0)
        else:
            self.sentimiento_usuario = 'neutral'
        
        # Si el nivel de frustración es alto, marcar para escalamiento
        if self.nivel_frustacion >= 3:
            self.requiere_escalamiento = True
            self.motivo_escalamiento = f"Alto nivel de frustración detectado ({self.nivel_frustacion}/10)"
        
        self.save()

class EstadisticasChatbot(models.Model):
    """Estadísticas y métricas del chatbot"""
    
    fecha = models.DateField(unique=True)
    
    # Métricas de conversaciones
    total_conversaciones = models.IntegerField(default=0)
    conversaciones_exitosas = models.IntegerField(default=0)  # Resueltas sin escalamiento
    conversaciones_escaladas = models.IntegerField(default=0)
    
    # Métricas de mensajes
    total_mensajes_usuario = models.IntegerField(default=0)
    total_mensajes_ia = models.IntegerField(default=0)
    
    # Métricas de rendimiento
    tiempo_respuesta_promedio = models.FloatField(default=0.0)  # En segundos
    confianza_promedio = models.FloatField(default=0.0)  # 0-1
    tokens_utilizados = models.IntegerField(default=0)
    
    # Métricas de satisfacción
    satisfaccion_promedio = models.FloatField(null=True, blank=True)  # 1-5
    porcentaje_escalamiento = models.FloatField(default=0.0)  # %
    
    # Temas más consultados
    temas_frecuentes = models.JSONField(default=dict, blank=True)  # {tema: count}
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Estadísticas Chatbot'
        verbose_name_plural = 'Estadísticas Chatbot'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Stats {self.fecha} - {self.total_conversaciones} conversaciones"

class SolicitudSoporte(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'), 
        ('rechazada', 'Rechazada'),
        ('en_chat', 'En Chat'),
        ('finalizada', 'Finalizada')
    ]
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    mensaje = models.TextField(blank=True, null=True)
    admin_asignado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_asignadas')

    def __str__(self):
        return f"Solicitud de {self.usuario.username} - {self.estado}"

# ====================================
# MODELOS DEL CHAT DIRECTO USUARIO-ADMIN
# ====================================

class ConversacionDirecta(models.Model):
    """Conversación directa entre usuario y administrador"""
    
    ESTADOS = [
        ('activa', 'Activa'),
        ('pausada', 'Pausada'),
        ('finalizada', 'Finalizada'),
    ]
    
    solicitud_soporte = models.OneToOneField(SolicitudSoporte, on_delete=models.CASCADE, related_name='conversacion_directa')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversaciones_usuario')
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversaciones_admin')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activa')
    session_id = models.CharField(max_length=100, unique=True)
    
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    fecha_ultima_actividad = models.DateTimeField(auto_now=True)
    
    # Metadatos
    total_mensajes = models.IntegerField(default=0)
    satisfaccion_usuario = models.IntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    notas_admin = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Conversación Directa'
        verbose_name_plural = 'Conversaciones Directas'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"Conversación {self.session_id} - {self.usuario.username} con {self.admin.username}"
    
    def finalizar(self, motivo="Conversación finalizada"):
        """Finaliza la conversación"""
        from django.utils import timezone
        self.estado = 'finalizada'
        self.fecha_fin = timezone.now()
        self.solicitud_soporte.estado = 'finalizada'
        self.solicitud_soporte.save()
        self.save()

class MensajeDirecto(models.Model):
    """Mensaje individual en una conversación directa"""
    
    conversacion = models.ForeignKey(ConversacionDirecta, on_delete=models.CASCADE, related_name='mensajes')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contenido = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    
    # Metadatos
    es_admin = models.BooleanField()  # True si el autor es admin
    editado = models.BooleanField(default=False)
    fecha_edicion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Mensaje Directo'
        verbose_name_plural = 'Mensajes Directos'
        ordering = ['timestamp']
    
    def __str__(self):
        tipo = "Admin" if self.es_admin else "Usuario"
        return f"{tipo}: {self.contenido[:50]}..."
    
    def save(self, *args, **kwargs):
        # Determinar si es admin basado en el rol del autor
        self.es_admin = self.autor.role in ['admin', 'superuser']
        super().save(*args, **kwargs)
        
        # Actualizar contador de mensajes
        self.conversacion.total_mensajes = self.conversacion.mensajes.count()
        self.conversacion.save()
