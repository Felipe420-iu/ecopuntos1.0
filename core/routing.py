from django.urls import re_path, path
from . import consumers
from .chatbot.consumers import ChatbotConsumer

websocket_urlpatterns = [
    # Chatbot IA - SIN USER_ID (se obtiene del usuario autenticado)
    path('ws/chatbot/', ChatbotConsumer.as_asgi()),
    
    # Chat global
    path('ws/chat/', consumers.ChatConsumer.as_asgi()),
    
    # Rutas existentes
    re_path(r'ws/notificaciones/(?P<user_id>\w+)/$', consumers.NotificacionConsumer.as_asgi()),
    re_path(r'ws/dashboard/(?P<user_id>\w+)/$', consumers.DashboardConsumer.as_asgi()),
    re_path(r'ws/canjes/(?P<user_id>\w+)/$', consumers.CanjeConsumer.as_asgi()),
]