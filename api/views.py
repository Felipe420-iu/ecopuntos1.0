from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
# Importar modelos
from core.models import (
    Usuario, MaterialTasa, Canje, RedencionPuntos, 
    Ruta, Alerta, Recompensa, Categoria, Logro, 
    Notificacion, SesionUsuario
)
from core.statistics import StatisticsManager
from .serializers import (
    UsuarioSerializer, MaterialTasaSerializer, CanjeSerializer,
    RedencionPuntosSerializer, RutaSerializer, AlertaSerializer,
    RecompensaSerializer, CategoriaSerializer, LogroSerializer,
    NotificacionSerializer, SesionUsuarioSerializer,
    EstadisticasUsuarioSerializer, EstadisticasGeneralesSerializer
)


class UsuarioViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar usuarios"""
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar usuarios según el rol del usuario autenticado"""
        user = self.request.user
        if user.role == 'admin':
            return Usuario.objects.all()
        elif user.role == 'recolector':
            return Usuario.objects.filter(role='usuario')
        else:
            return Usuario.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def perfil(self, request):
        """Obtener perfil del usuario autenticado"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'])
    def actualizar_perfil(self, request):
        """Actualizar perfil del usuario autenticado"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        """Obtener estadísticas de un usuario específico"""
        usuario = self.get_object()
        
        # Usar cache para estadísticas
        cache_key = f'user_stats_{usuario.id}'
        stats = cache.get(cache_key)
        
        if not stats:
            stats = {
                'total_puntos': usuario.puntos,
                'total_canjes': Canje.objects.filter(usuario=usuario).count(),
                'total_redenciones': RedencionPuntos.objects.filter(usuario=usuario).count(),
                'materiales_reciclados': dict(
                    Canje.objects.filter(usuario=usuario)
                    .values('material__nombre')
                    .annotate(total=Sum('cantidad'))
                    .values_list('material__nombre', 'total')
                ),
                'logros_obtenidos': Logro.objects.filter(usuario=usuario).count(),
                'ranking_posicion': Usuario.objects.filter(puntos__gt=usuario.puntos).count() + 1
            }
            cache.set(cache_key, stats, 300)  # Cache por 5 minutos
        
        serializer = EstadisticasUsuarioSerializer(stats)
        return Response(serializer.data)


class MaterialTasaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar materiales y tasas"""
    queryset = MaterialTasa.objects.all()
    serializer_class = MaterialTasaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Solo admins pueden crear/editar/eliminar materiales"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class CanjeViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar canjes de materiales"""
    queryset = Canje.objects.all()
    serializer_class = CanjeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar canjes según el rol del usuario"""
        user = self.request.user
        if user.role == 'admin':
            return Canje.objects.all()
        elif user.role == 'recolector':
            return Canje.objects.all()
        else:
            return Canje.objects.filter(usuario=user)
    
    def perform_create(self, serializer):
        """Asignar usuario autenticado al crear canje"""
        serializer.save(usuario=self.request.user)
    
    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprobar un canje (solo recolectores y admins)"""
        if request.user.role not in ['recolector', 'admin']:
            return Response(
                {'error': 'No tienes permisos para aprobar canjes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        canje = self.get_object()
        if canje.estado != 'pendiente':
            return Response(
                {'error': 'El canje ya ha sido procesado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener peso real y puntos del request
        peso_real = request.data.get('peso_real', canje.peso)
        puntos = request.data.get('puntos')
        
        try:
            # Validar peso real
            peso_real = float(peso_real)
            if peso_real <= 0:
                return Response(
                    {'error': 'El peso debe ser mayor a 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Actualizar el canje
            canje.estado = 'aprobado'
            canje.peso = peso_real
            
            # Calcular puntos si no se proporcionaron
            if puntos:
                puntos_ganados = int(puntos)
            else:
                puntos_ganados = int(peso_real * canje.material.puntos_por_kilo)
            
            canje.puntos = puntos_ganados
            canje.usuario.puntos += puntos_ganados
            canje.usuario.save()
            canje.save()
            
            # Enviar correo de confirmación de canje aprobado
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                
                subject = f'¡Canje Aprobado! +{puntos_ganados} puntos - EcoPuntos'
                message = f"""
Hola {canje.usuario.first_name or canje.usuario.username},

¡Excelentes noticias! Tu canje ha sido aprobado por nuestro equipo.

Detalles del canje aprobado:
- Material: {canje.material.nombre}
- Peso procesado: {peso_real} kg
- Puntos otorgados: {puntos_ganados}

Los puntos han sido agregados automáticamente a tu cuenta.

¡Gracias por reciclar y sumar puntos ecológicos!

Equipo EcoPuntos
"""
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [canje.usuario.email],
                    fail_silently=False,
                )
                print(f"✅ Email de canje aprobado enviado exitosamente a {canje.usuario.email}")
            except Exception as e:
                # Si falla el correo, continuar sin interrumpir el proceso
                print(f"❌ Error enviando correo de canje aprobado: {e}")
                import traceback
                traceback.print_exc()
            
            # Invalidar cache de estadísticas
            cache.delete(f'user_stats_{canje.usuario.id}')
            
            return Response({
                'message': 'Canje aprobado exitosamente',
                'peso_real': peso_real,
                'puntos_ganados': puntos_ganados,
                'usuario': canje.usuario.username
            })
            
        except ValueError:
            return Response(
                {'error': 'Peso inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        """Rechazar un canje (solo recolectores y admins)"""
        if request.user.role not in ['recolector', 'admin']:
            return Response(
                {'error': 'No tienes permisos para rechazar canjes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        canje = self.get_object()
        if canje.estado != 'pendiente':
            return Response(
                {'error': 'El canje ya ha sido procesado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        canje.estado = 'rechazado'
        canje.save()
        
        # Invalidar cache de estadísticas
        cache.delete(f'user_stats_{canje.usuario.id}')
        
        return Response({'message': 'Canje rechazado exitosamente'})


class RedencionPuntosViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar redenciones de puntos"""
    queryset = RedencionPuntos.objects.all()
    serializer_class = RedencionPuntosSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar redenciones según el rol del usuario"""
        user = self.request.user
        if user.role == 'admin':
            return RedencionPuntos.objects.all()
        else:
            return RedencionPuntos.objects.filter(usuario=user)
    
    def perform_create(self, serializer):
        """Asignar usuario autenticado al crear redención"""
        serializer.save(usuario=self.request.user)


class RutaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar rutas de recolección"""
    queryset = Ruta.objects.all()
    serializer_class = RutaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Solo admins y recolectores pueden gestionar rutas"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """Obtener rutas disponibles para hoy y mañana"""
        hoy = timezone.now().date()
        manana = hoy + timedelta(days=1)
        
        rutas = Ruta.objects.filter(
            fecha__in=[hoy, manana],
            estado='programada'
        ).order_by('fecha', 'hora_inicio')
        
        serializer = self.get_serializer(rutas, many=True)
        return Response(serializer.data)


class NotificacionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar notificaciones"""
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        """Obtener todas las notificaciones del usuario"""
        notificaciones = self.get_queryset()
        serializer = self.get_serializer(notificaciones, many=True)
        return Response({
            'success': True,
            'notifications': serializer.data
        })
    
    def get_queryset(self):
        """Filtrar notificaciones del usuario autenticado"""
        return Notificacion.objects.filter(usuario=self.request.user).order_by('-fecha_creacion')
    
    @action(detail=False, methods=['get'])
    def no_leidas(self, request):
        """Obtener notificaciones no leídas"""
        notificaciones = self.get_queryset().filter(leida=False)
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def marcar_leida(self, request, pk=None):
        """Marcar notificación como leída"""
        notificacion = self.get_object()
        notificacion.leida = True
        notificacion.save()
        return Response({'message': 'Notificación marcada como leída'})
    
    @action(detail=False, methods=['post'])
    def marcar_todas_leidas(self, request):
        """Marcar todas las notificaciones como leídas"""
        count = self.get_queryset().filter(leida=False).count()
        self.get_queryset().update(leida=True)
        return Response({
            'success': True,
            'message': f'Se marcaron {count} notificaciones como leídas'
        })
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Obtener notificaciones para el dashboard con contador de no leídas"""
        notificaciones = self.get_queryset()[:10]  # Últimas 10 notificaciones
        unread_count = self.get_queryset().filter(leida=False).count()
        
        serializer = self.get_serializer(notificaciones, many=True)
        return Response({
            'notifications': serializer.data,
            'unread_count': unread_count
        })
    
    @action(detail=False, methods=['post'])
    def marcar_leidas(self, request):
        """Marcar notificaciones no leídas como leídas (para cuando se abre el modal)"""
        self.get_queryset().filter(leida=False).update(leida=True)
        return Response({'message': 'Notificaciones marcadas como leídas'})
    
    @action(detail=False, methods=['post'])
    def vaciar_todas(self, request):
        """Eliminar todas las notificaciones del usuario"""
        count = self.get_queryset().count()
        self.get_queryset().delete()
        return Response({
            'success': True,
            'message': f'Se eliminaron {count} notificaciones'
        })


class EstadisticasAPIView(APIView):
    """Vista para obtener estadísticas generales del sistema"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtener estadísticas generales"""
        # Usar cache para estadísticas generales
        cache_key = 'general_stats'
        stats = cache.get(cache_key)
        
        if not stats:
            stats_manager = StatisticsManager()
            stats = {
                'usuarios_activos': stats_manager.get_daily_active_users(),
                'total_canjes_mes': Canje.objects.filter(
                    fecha__gte=timezone.now().replace(day=1)
                ).count(),
                'total_puntos_otorgados': Usuario.objects.aggregate(
                    total=Sum('puntos')
                )['total'] or 0,
                'material_mas_reciclado': stats_manager.get_recycling_stats_by_material().get('most_recycled', 'N/A'),
                'usuarios_nuevos_mes': Usuario.objects.filter(
                    date_joined__gte=timezone.now().replace(day=1)
                ).count()
            }
            cache.set(cache_key, stats, 600)  # Cache por 10 minutos
        
        serializer = EstadisticasGeneralesSerializer(stats)
        return Response(serializer.data)


class RankingAPIView(APIView):
    """Vista para obtener ranking de usuarios"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtener ranking de usuarios por puntos"""
        limit = int(request.query_params.get('limit', 10))
        
        usuarios = Usuario.objects.filter(
            role='usuario'
        ).order_by('-puntos')[:limit]
        
        ranking_data = []
        for i, usuario in enumerate(usuarios, 1):
            ranking_data.append({
                'posicion': i,
                'usuario': UsuarioSerializer(usuario).data,
                'puntos': usuario.puntos
            })
        
        return Response(ranking_data)


class DashboardAPIView(APIView):
    """Vista para obtener datos del dashboard"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtener datos completos del dashboard"""
        user = request.user
        
        if user.role == 'admin':
            # Dashboard de administrador
            stats_manager = StatisticsManager()
            dashboard_data = {
                'estadisticas_generales': stats_manager.get_dashboard_stats(),
                'canjes_pendientes': Canje.objects.filter(estado='pendiente').count(),
                'redenciones_pendientes': RedencionPuntos.objects.filter(estado='pendiente').count(),
                'usuarios_activos_hoy': stats_manager.get_daily_active_users(),
                'alertas_activas': Alerta.objects.filter(activa=True).count()
            }
        else:
            # Dashboard de usuario
            dashboard_data = {
                'puntos_totales': user.puntos,
                'canjes_mes': Canje.objects.filter(
                    usuario=user,
                    fecha__gte=timezone.now().replace(day=1)
                ).count(),
                'notificaciones_no_leidas': Notificacion.objects.filter(
                    usuario=user, leida=False
                ).count(),
                'ranking_posicion': Usuario.objects.filter(
                    puntos__gt=user.puntos
                ).count() + 1,
                'rutas_disponibles': Ruta.objects.filter(
                    fecha__gte=timezone.now().date(),
                    estado='programada'
                ).count()
            }
        
        return Response(dashboard_data)