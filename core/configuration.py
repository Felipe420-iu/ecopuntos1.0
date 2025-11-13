from django.db import models

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
