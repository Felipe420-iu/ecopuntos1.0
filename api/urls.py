from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    UsuarioViewSet, MaterialTasaViewSet, CanjeViewSet,
    RedencionPuntosViewSet, RutaViewSet, NotificacionViewSet,
    EstadisticasAPIView, RankingAPIView, DashboardAPIView
)

# Crear router para ViewSets
router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'materiales', MaterialTasaViewSet)
router.register(r'canjes', CanjeViewSet)
router.register(r'redenciones', RedencionPuntosViewSet)
router.register(r'rutas', RutaViewSet)
router.register(r'notificaciones', NotificacionViewSet)

app_name = 'api'

urlpatterns = [
    # Autenticación JWT
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Endpoints de ViewSets
    path('', include(router.urls)),
    
    # Endpoints personalizados
    path('estadisticas/', EstadisticasAPIView.as_view(), name='estadisticas'),
    path('ranking/', RankingAPIView.as_view(), name='ranking'),
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard'),
    
    # Documentación de la API (opcional)
    path('docs/', include('rest_framework.urls', namespace='rest_framework')),
]

# URLs adicionales para funcionalidades específicas
urlpatterns += [
    # Endpoints específicos para usuarios
    path('usuarios/perfil/', UsuarioViewSet.as_view({'get': 'perfil'}), name='usuario-perfil'),
    path('usuarios/actualizar-perfil/', UsuarioViewSet.as_view({'put': 'actualizar_perfil'}), name='usuario-actualizar-perfil'),
    
    # Endpoints específicos para canjes
    path('canjes/<int:pk>/aprobar/', CanjeViewSet.as_view({'post': 'aprobar'}), name='canje-aprobar'),
    path('canjes/<int:pk>/rechazar/', CanjeViewSet.as_view({'post': 'rechazar'}), name='canje-rechazar'),
    
    # Endpoints específicos para rutas
    path('rutas/disponibles/', RutaViewSet.as_view({'get': 'disponibles'}), name='rutas-disponibles'),
    
    # Endpoints específicos para notificaciones
    path('notificaciones/no-leidas/', NotificacionViewSet.as_view({'get': 'no_leidas'}), name='notificaciones-no-leidas'),
    path('notificaciones/<int:pk>/marcar-leida/', NotificacionViewSet.as_view({'post': 'marcar_leida'}), name='notificacion-marcar-leida'),
    path('notificaciones/marcar-todas-leidas/', NotificacionViewSet.as_view({'post': 'marcar_todas_leidas'}), name='notificaciones-marcar-todas-leidas'),
    path('notificaciones/vaciar-todas/', NotificacionViewSet.as_view({'post': 'vaciar_todas'}), name='notificaciones-vaciar-todas'),
]