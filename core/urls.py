from django.urls import path
from . import views
from . import views_superuser
from .redemptions import get_pending_redemptions, aprobar_redencion, rechazar_redencion
from . import password_recovery
from . import security
from .chatbot import views as chatbot_views

urlpatterns = [
    path('', views.index, name='index'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_ajax, name='login_ajax'),
    path('registrate/', views.registrate, name='registrate'),
    path('verificar-email/', views.verificar_email, name='verificar_email'),
    path('terminos-condiciones/', views.terminos_condiciones, name='terminos_condiciones'),
    path('politica-privacidad/', views.politica_privacidad, name='politica_privacidad'),
    path('iniciosesion/', views.iniciosesion, name='iniciosesion'),
    path('perfil/', views.perfil, name='perfil'),
    path('notificaciones/', views.notificaciones, name='notificaciones'),
    path('categorias/', views.categorias, name='categorias'),
    path('juego-plasticos/', views.juego_plasticos, name='juego_plasticos'),
    path('juego-vidrios/', views.juego_vidrios, name='juego_vidrios'),
    path('juego-papel/', views.juego_papel, name='juego_papel'),
    path('juego-metales/', views.juego_metales, name='juego_metales'),
    path('canjes/', views.canjes, name='canjes'),  # Show the form
    path('canjes/submit/', views.solicitar_canje, name='solicitar_canje'),  # Handle form submission
    path('historial/', views.historial, name='historial'),
    path('logros/', views.logros, name='logros'),
    # Edición AJAX superusuario
    path('superuser/obtener-usuario/<int:user_id>/', views_superuser.obtener_usuario_superuser, name='obtener_usuario_superuser'),
    path('superuser/editar-usuario/<int:user_id>/', views_superuser.editar_usuario_superuser, name='editar_usuario_superuser'),
    path('superuser/eliminar-usuario/<int:user_id>/', views_superuser.eliminar_usuario_superuser, name='eliminar_usuario_superuser'),
    path('recompensas/', views.recompensas, name='recompensas'),

    path('pagos/', views.pagos, name='pagos'),
    path('redimir_puntos/', views.redimir_puntos, name='redimir_puntos'),
    path('test_email/', views.test_email_config, name='test_email'),  # URL temporal para testing
    path('usuarioadmin/', views.usuarioadmin, name='usuarioadmin'),
    path('canjeadmin/', views.canjeadmin, name='canjeadmin'),
    path('dashusuario/', views.dashusuario, name='dashusuario'),
    path('paneladmin/', views.paneladmin, name='paneladmin'),
    path('panel_conductor/', views.panel_conductor, name='panel_conductor'),
    
    # APIs para conductor
    path('api/conductor/estadisticas/', views.conductor_estadisticas, name='conductor_estadisticas'),
    path('api/conductor/graficas/', views.conductor_graficas, name='conductor_graficas'),
    
    path('rutas/', views.rutas, name='rutas'),
    path('inicioadmin/', views.inicioadmin, name='inicioadmin'),
    path('aprobar-canje/<int:canje_id>/', views.aprobar_canje, name='aprobar_canje'),
    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),
    path('reset-password/<str:token>/', password_recovery.reset_password, name='reset_password'),

    path('add_ruta/', views.add_ruta, name='add_ruta'),
    path('edit_ruta/<int:ruta_id>/', views.edit_ruta, name='edit_ruta'),
    path('delete_ruta/<int:ruta_id>/', views.delete_ruta, name='delete_ruta'),
    path('confirmar_ruta/<int:ruta_id>/', views.confirmar_ruta, name='confirmar_ruta'),
    path('rechazar_ruta/<int:ruta_id>/', views.rechazar_ruta, name='rechazar_ruta'),
    path('reagendar_ruta/<int:ruta_id>/', views.reagendar_ruta, name='reagendar_ruta'),

    path('estadisticasadmin/', views.estadisticasadmin, name='estadisticasadmin'),

    path('add_alerta/', views.add_alerta, name='add_alerta'),
    path('edit_alerta/', views.edit_alerta, name='edit_alerta'),
    path('delete_alerta/', views.delete_alerta, name='delete_alerta'),

    path('get_dashboard_stats/', views.get_dashboard_stats, name='get_dashboard_stats'),
    path('get-pending-canjes/', views.get_pending_canjes, name='get_pending_canjes'),
    path('get-pending-canjes-admin/', views.get_pending_canjes_for_admin, name='get_pending_canjes_for_admin'),
    path('aprobar_canje_ajax/', views.aprobar_canje, name='aprobar_canje_ajax'),
    
    # API v1 para canjes
    path('api/v1/canjes/<int:canje_id>/aprobar/', views.aprobar_canje_peso_real, name='aprobar_canje_peso_real'),
    path('api/v1/canjes/<int:canje_id>/rechazar/', views.rechazar_canje_ajax, name='rechazar_canje_ajax'),
    
    # URLs del monitor de sesiones
    path('admin/monitor-sesiones/', views.monitor_sesiones, name='monitor_sesiones'),
    path('admin/monitor-sesiones/refresh/', views.monitor_sesiones_refresh, name='monitor_sesiones_refresh'),
    path('admin/monitor-sesiones/terminar/<str:session_id>/', views.terminar_sesion, name='terminar_sesion'),
    path('admin/monitor-sesiones/limpiar/', views.limpiar_sesiones, name='limpiar_sesiones'),
    path('usuario-desactivado/', views.usuario_desactivado, name='usuario_desactivado'),
    path('usuario-suspendido/', views.usuario_suspendido, name='usuario_suspendido'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('deactivate_user/<int:user_id>/', views.deactivate_user, name='deactivate_user'),
    path('suspend_user/<int:user_id>/', views.suspend_user, name='suspend_user'),
    path('reactivate_user/<int:user_id>/', views.reactivate_user, name='reactivate_user'),
    path('unsuspend_user/<int:user_id>/', views.unsuspend_user, name='unsuspend_user'),
    path('verificar-sesion/', views.verificar_sesion_activa, name='verificar_sesion_activa'),
    path('usuario-desactivado/', views.usuario_desactivado, name='usuario_desactivado'),
    path('usuario-suspendido/', views.usuario_suspendido, name='usuario_suspendido'),
    path('get_chart_data/', views.get_chart_data, name='get_chart_data'),
    path('admin/canje/<int:canje_id>/procesar/', views.procesar_canje, name='procesar_canje'),
    path('rutasusuario/', views.rutasusuario, name='rutasusuario'),
    path('rutasusuario/reagendada/<int:ruta_id>/', views.rutasusuario_reagendada, name='rutasusuario_reagendada'),
    path('agendar_ruta_usuario/', views.agendar_ruta_usuario, name='agendar_ruta_usuario'),
    # Nuevas rutas
    path('ranking/', views.ranking, name='ranking'),
    
    # SISTEMA DE CHATBOT CON IA (URLs consolidadas)
    path('chatbot/', chatbot_views.chatbot_view, name='chatbot_interface'),  # URL principal
    path('chatbot/historial/', chatbot_views.historial_conversaciones, name='historial_chatbot'),
    path('chatbot/conversacion/<int:conversacion_id>/', chatbot_views.ver_conversacion, name='ver_conversacion_chatbot'),
    path('chatbot/status/', chatbot_views.check_chatbot_status, name='chatbot_status'),
    path('chatbot/soporte/', chatbot_views.chatbot_soporte, name='chat_soporte'),
    path('chatbot/escalar/', chatbot_views.escalar_a_humano, name='escalar_a_humano'),
    
    # APIs para integración de chat directo con el chatbot del usuario
    path('api/chat-directo/verificar/', chatbot_views.verificar_chat_directo, name='verificar_chat_directo'),
    path('api/chat-directo/enviar-mensaje/', chatbot_views.enviar_mensaje_usuario_a_chat, name='enviar_mensaje_usuario_chat'),
    path('api/chat-directo/obtener-mensajes/', chatbot_views.obtener_mensajes_chat_directo, name='obtener_mensajes_chat_directo'),
    
    # URLs para administración de solicitudes de soporte
    path('admin/solicitudes-soporte/', chatbot_views.listar_solicitudes_soporte, name='listar_solicitudes_soporte'),
    path('admin/solicitud-soporte/<int:solicitud_id>/', chatbot_views.gestionar_solicitud, name='gestionar_solicitud'),
    
    # URLs para chat directo usuario-admin
    path('admin/conversaciones-activas/', chatbot_views.listar_conversaciones_activas, name='conversaciones_activas'),
    path('chat-directo/<int:conversation_id>/', chatbot_views.chat_directo, name='chat_directo'),
    path('chat-directo/<int:conversation_id>/enviar/', chatbot_views.enviar_mensaje_directo, name='enviar_mensaje_directo'),
    path('chat-directo/<int:conversation_id>/finalizar/', chatbot_views.finalizar_chat_directo, name='finalizar_chat_directo'),
    
    # Aliases antiguos para compatibilidad - todos redirigen a chatbot_interface
    path('soportusu/', views.redirect_to_chatbot, name='soportusu'),

    path('admin/redemptions/', get_pending_redemptions, name='get_pending_redemptions'),
    path('admin/redemptions/<int:redencion_id>/approve/', aprobar_redencion, name='aprobar_redencion'),
    path('admin/redemptions/<int:redencion_id>/reject/', rechazar_redencion, name='rechazar_redencion'),
    path('retiroadmin/', views.retiroadmin, name='retiroadmin'),
    path('stock-recompensas/', views.stock_recompensas, name='stock_recompensas'),
    path('stock/editar/<int:recompensa_id>/', views.editar_stock_recompensa, name='editar_stock_recompensa'),
    path('stock/toggle/<int:recompensa_id>/', views.toggle_recompensa, name='toggle_recompensa'),
    path('stock/agregar/', views.agregar_recompensa, name='agregar_recompensa'),
    path('stock/historial/<int:recompensa_id>/', views.historial_stock, name='historial_stock'),
    path('stock/reabastecer/<int:recompensa_id>/', views.reabastecer_stock, name='reabastecer_stock'),
    # Nuevas rutas para estadísticas avanzadas y seguridad
    path('security-analytics/', views.get_security_analytics, name='get_security_analytics'),

    # APIs para recuperación de contraseña
    path('api/password-recovery/send-code/', password_recovery.send_verification_code, name='password_recovery_send_code'),
    path('api/password-recovery/verify-code/', password_recovery.verify_code, name='password_recovery_verify_code'),
    path('api/password-recovery/reset-password/', password_recovery.reset_password, name='password_recovery_reset_password'),

    path('cleanup-sessions/', views.cleanup_expired_sessions, name='cleanup_expired_sessions'),
    path('security-monitor/', views.security_monitor, name='security_monitor'),
    # Nuevas rutas para monitoreo de sesiones
    path('admin/monitor-sesiones/', views.monitor_sesiones, name='monitor_sesiones'),
    path('admin/cerrar-sesion/<int:session_id>/', views.cerrar_sesion_admin, name='cerrar_sesion_admin'),
    path('admin/limpiar-sesiones/', views.limpiar_sesiones_admin, name='limpiar_sesiones_admin'),

    
    # APIs para recuperación de contraseña
    path('api/password-recovery/send-code/', password_recovery.send_verification_code, name='send_verification_code'),
    path('api/password-recovery/verify-code/', password_recovery.verify_code, name='verify_code'),
    path('api/password-recovery/reset-password/', password_recovery.reset_password, name='reset_password'),
    path('api/password-recovery/check-email/', password_recovery.check_email_exists, name='check_email_exists'),
    
    # APIs para términos y condiciones
    path('api/aceptar-terminos/', views.aceptar_terminos, name='aceptar_terminos'),
    path('api/verificar-terminos/', views.verificar_terminos, name='verificar_terminos'),
    
    # APIs para reagendamientos
    path('api/verificar-reagendamientos/', views.verificar_reagendamientos_pendientes, name='verificar_reagendamientos_pendientes'),
    path('api/marcar-reagendamiento-visto/', views.marcar_reagendamiento_visto, name='marcar_reagendamiento_visto'),
    
    # APIs para notificaciones
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/clear/', views.delete_all_notifications, name='delete_all_notifications'),
    path('api/notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/v1/notificaciones/marcar-leidas/', views.mark_all_notifications_read, name='mark_notifications_read_v1'),
    path('api/v1/notificaciones/marcar-todas-leidas/', views.mark_all_notifications_read, name='mark_all_notifications_read_v1'),
    
    # URLs de chatbot están definidas arriba - sección consolidada
    
    # Página de prueba del chat WebSocket
    path('test-chat/', views.test_chat, name='test_chat'),
    
    # URLs de integración removidas - funcionalidad integrada en canjes y rutas principales
    
    # URLs del Superusuario
    path('superuser/', views_superuser.panel_superuser, name='panel_superuser'),
    path('superuser/usuarios/', views_superuser.gestion_usuarios_superuser, name='gestion_usuarios_superuser'),
    path('superuser/usuarios/crear/', views_superuser.crear_usuario_superuser, name='crear_usuario_superuser'),
    path('superuser/usuarios/eliminar/<int:user_id>/', views_superuser.eliminar_usuario_superuser, name='eliminar_usuario_superuser'),
    path('superuser/cambiar-rol/<int:user_id>/', views_superuser.cambiar_rol_usuario, name='cambiar_rol_usuario'),
    path('superuser/admins/', views_superuser.gestion_admins_superuser, name='gestion_admins_superuser'),
    path('superuser/promover-admin/<int:user_id>/', views_superuser.promover_a_admin, name='promover_a_admin'),
    path('superuser/degradar-admin/<int:user_id>/', views_superuser.degradar_admin, name='degradar_admin'),
    path('superuser/configuracion/', views_superuser.configuracion_sistema_superuser, name='configuracion_sistema_superuser'),
    
    # URLs del Sistema de Seguimiento de Recompensas
    path('api/seguimiento/actualizar/<int:seguimiento_id>/', views.actualizar_estado_seguimiento, name='actualizar_estado_seguimiento'),
    path('admin/seguimientos/', views.listar_seguimientos_admin, name='listar_seguimientos_admin'),
    path('seguimiento/<str:codigo_seguimiento>/', views.detalle_seguimiento, name='detalle_seguimiento'),
    path('api/seguimiento/foto/<int:seguimiento_id>/', views.subir_foto_entrega, name='subir_foto_entrega'),
    path('api/seguimiento/calificar/<int:seguimiento_id>/', views.calificar_servicio, name='calificar_servicio'),
    
    # Endpoint para generar notificación de prueba
    path('api/test-notification/', views.crear_notificacion_prueba, name='crear_notificacion_prueba'),
]

