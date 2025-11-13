from rest_framework import serializers
from core.models import (
    Usuario, MaterialTasa, Canje, RedencionPuntos, 
    Ruta, Alerta, Recompensa, Categoria, Logro, 
    Notificacion, SesionUsuario
)


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Usuario"""
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'puntos', 'telefono', 'direccion', 'testimonio',
            'notificaciones_email', 'notificaciones_sms', 'date_joined',
            'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'puntos': {'read_only': True},
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class MaterialTasaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo MaterialTasa"""
    
    class Meta:
        model = MaterialTasa
        fields = '__all__'


class CanjeSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Canje"""
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    material_nombre = serializers.CharField(source='material.nombre', read_only=True)
    
    class Meta:
        model = Canje
        fields = [
            'id', 'usuario', 'usuario_nombre', 'material', 'material_nombre',
            'cantidad', 'puntos_ganados', 'fecha', 'estado', 'observaciones'
        ]
        read_only_fields = ['puntos_ganados', 'fecha']


class RedencionPuntosSerializer(serializers.ModelSerializer):
    """Serializer para el modelo RedencionPuntos"""
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    
    class Meta:
        model = RedencionPuntos
        fields = [
            'id', 'usuario', 'usuario_nombre', 'puntos_canjeados',
            'valor_cop', 'metodo_pago', 'estado', 'fecha_solicitud',
            'fecha_procesamiento', 'observaciones'
        ]
        read_only_fields = ['fecha_solicitud', 'fecha_procesamiento']


class RutaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Ruta"""
    materiales_nombres = serializers.StringRelatedField(source='materiales', many=True, read_only=True)
    
    class Meta:
        model = Ruta
        fields = [
            'id', 'nombre', 'descripcion', 'fecha', 'hora_inicio',
            'hora_fin', 'ubicacion', 'materiales', 'materiales_nombres',
            'capacidad_maxima', 'estado', 'observaciones'
        ]


class AlertaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Alerta"""
    
    class Meta:
        model = Alerta
        fields = '__all__'


class RecompensaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Recompensa"""
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    
    class Meta:
        model = Recompensa
        fields = [
            'id', 'nombre', 'descripcion', 'puntos_requeridos',
            'categoria', 'categoria_nombre', 'imagen', 'disponible',
            'fecha_creacion'
        ]


class CategoriaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Categoria"""
    
    class Meta:
        model = Categoria
        fields = '__all__'


class LogroSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Logro"""
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    
    class Meta:
        model = Logro
        fields = [
            'id', 'usuario', 'usuario_nombre', 'titulo', 'descripcion',
            'puntos_otorgados', 'fecha_obtencion', 'icono'
        ]


class NotificacionSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Notificacion"""
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    
    class Meta:
        model = Notificacion
        fields = [
            'id', 'usuario', 'usuario_nombre', 'titulo', 'mensaje',
            'tipo', 'leida', 'fecha_creacion'
        ]


class SesionUsuarioSerializer(serializers.ModelSerializer):
    """Serializer para el modelo SesionUsuario"""
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    
    class Meta:
        model = SesionUsuario
        fields = [
            'id', 'usuario', 'usuario_nombre', 'token', 'device_id',
            'ip_address', 'user_agent', 'fecha_creacion', 'fecha_expiracion',
            'activa'
        ]
        read_only_fields = ['token', 'fecha_creacion']


# Serializers específicos para estadísticas
class EstadisticasUsuarioSerializer(serializers.Serializer):
    """Serializer para estadísticas de usuario"""
    total_puntos = serializers.IntegerField()
    total_canjes = serializers.IntegerField()
    total_redenciones = serializers.IntegerField()
    materiales_reciclados = serializers.DictField()
    logros_obtenidos = serializers.IntegerField()
    ranking_posicion = serializers.IntegerField()


class EstadisticasGeneralesSerializer(serializers.Serializer):
    """Serializer para estadísticas generales del sistema"""
    usuarios_activos = serializers.IntegerField()
    total_canjes_mes = serializers.IntegerField()
    total_puntos_otorgados = serializers.IntegerField()
    material_mas_reciclado = serializers.CharField()
    usuarios_nuevos_mes = serializers.IntegerField()