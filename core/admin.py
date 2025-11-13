from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Canje, MaterialTasa, RedencionPuntos, Recompensa, Categoria, FavoritoRecompensa, Logro, Notificacion

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'puntos', 'fecha_registro')
    list_filter = ('role', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('role', 'puntos', 'telefono', 'direccion')
        }),
    )

class MaterialTasaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'puntos_por_kilo', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)

class CanjeAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'material', 'peso', 'puntos', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'material', 'fecha_solicitud')
    search_fields = ('usuario__username', 'material__nombre')
    readonly_fields = ('puntos',)
    actions = ['aprobar_canjes', 'rechazar_canjes', 'marcar_en_revision']
    
    def save_model(self, request, obj, form, change):
        # Guardar estado anterior para comparar
        estado_anterior = None
        if change:
            try:
                estado_anterior = Canje.objects.get(pk=obj.pk).estado
            except Canje.DoesNotExist:
                estado_anterior = None
        
        # Guardar el objeto
        super().save_model(request, obj, form, change)
        
        # Enviar notificación si el estado cambió
        if change and estado_anterior != obj.estado:
            self._enviar_notificacion_cambio_estado(obj, estado_anterior)
    
    def _enviar_notificacion_cambio_estado(self, canje, estado_anterior):
        """Envía notificación por email cuando cambia el estado del canje"""
        from .notifications import NotificacionEmail
        
        try:
            if canje.estado == 'aprobado':
                NotificacionEmail.notificar_canje_aprobado(canje)
            elif canje.estado == 'en_revision':
                NotificacionEmail.notificar_canje_en_revision(canje)
            elif canje.estado == 'rechazado':
                NotificacionEmail.notificar_canje_rechazado(canje)
        except Exception as e:
            self.message_user(request, f"Error enviando notificación: {e}", level='WARNING')
    
    def aprobar_canjes(self, request, queryset):
        """Acción personalizada para aprobar canjes en lote"""
        updated = 0
        for canje in queryset:
            if canje.estado != 'aprobado':
                canje.estado = 'aprobado'
                canje.save()
                
                # Agregar puntos al usuario
                canje.usuario.puntos += canje.puntos
                canje.usuario.save()
                
                # Enviar notificación
                try:
                    from .notifications import NotificacionEmail
                    NotificacionEmail.notificar_canje_aprobado(canje)
                except:
                    pass
                    
                updated += 1
        
        self.message_user(request, f"{updated} canjes aprobados exitosamente.")
    aprobar_canjes.short_description = "Aprobar canjes seleccionados"
    
    def rechazar_canjes(self, request, queryset):
        """Acción personalizada para rechazar canjes en lote"""
        updated = queryset.update(estado='rechazado')
        
        # Enviar notificaciones
        for canje in queryset:
            try:
                from .notifications import NotificacionEmail
                NotificacionEmail.notificar_canje_rechazado(canje)
            except:
                pass
        
        self.message_user(request, f"{updated} canjes rechazados.")
    rechazar_canjes.short_description = "Rechazar canjes seleccionados"
    
    def marcar_en_revision(self, request, queryset):
        """Acción personalizada para marcar canjes en revisión"""
        updated = queryset.update(estado='en_revision')
        
        # Enviar notificaciones
        for canje in queryset:
            try:
                from .notifications import NotificacionEmail
                NotificacionEmail.notificar_canje_en_revision(canje)
            except:
                pass
        
        self.message_user(request, f"{updated} canjes marcados en revisión.")
    marcar_en_revision.short_description = "Marcar como en revisión"

class RedencionPuntosAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'puntos', 'valor_cop', 'metodo_pago', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'metodo_pago', 'fecha_solicitud')
    search_fields = ('usuario__username', 'numero_cuenta')
    readonly_fields = ('valor_cop',)

class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre',)

class RecompensaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'puntos_requeridos', 'stock', 'es_popular', 'es_nuevo', 'es_oferta', 'activa')
    list_filter = ('categoria', 'es_popular', 'es_nuevo', 'es_oferta', 'activa')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('veces_canjeada', 'fecha_creacion')
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'imagen', 'categoria')
        }),
        ('Configuración de Puntos', {
            'fields': ('puntos_requeridos', 'stock')
        }),
        ('Características', {
            'fields': ('es_popular', 'es_nuevo', 'es_oferta', 'activa')
        }),
        ('Fechas y Estadísticas', {
            'fields': ('fecha_vencimiento', 'veces_canjeada', 'fecha_creacion'),
            'classes': ('collapse',)
        })
    )

class FavoritoRecompensaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'recompensa', 'fecha_agregado')
    list_filter = ('fecha_agregado',)
    search_fields = ('usuario__username', 'recompensa__nombre')

class LogroAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'descripcion', 'puntos', 'fecha_creacion')
    list_filter = ('tipo', 'fecha_creacion')
    search_fields = ('usuario__username', 'tipo', 'descripcion')

class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'titulo', 'tipo', 'leida', 'fecha_creacion')
    list_filter = ('tipo', 'leida', 'fecha_creacion')
    search_fields = ('usuario__username', 'titulo', 'mensaje')

admin.site.register(Usuario, CustomUserAdmin)
admin.site.register(MaterialTasa, MaterialTasaAdmin)
admin.site.register(Canje, CanjeAdmin)
admin.site.register(RedencionPuntos, RedencionPuntosAdmin)
admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Recompensa, RecompensaAdmin)
admin.site.register(FavoritoRecompensa, FavoritoRecompensaAdmin)
admin.site.register(Logro, LogroAdmin)
admin.site.register(Notificacion, NotificacionAdmin)
