from rest_framework import serializers
from .models import SesionUsuario

class SesionUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = SesionUsuario
        fields = ['id', 'token_sesion', 'fecha_creacion', 'ultima_actividad', 'ip_address', 'dispositivo', 'ubicacion', 'activa']
