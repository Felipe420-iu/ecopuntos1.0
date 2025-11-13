"""
Script de prueba para verificar que el chatbot funciona con Gemini 2.5 Flash
"""
import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto2023.settings')
django.setup()

from core.chatbot.services import get_ai_service

def test_chatbot():
    print("=" * 70)
    print("PRUEBA DEL CHATBOT CON GEMINI 2.5 FLASH")
    print("=" * 70)
    
    try:
        # Obtener el servicio de IA
        service = get_ai_service()
        print(f"\n[OK] Servicio de IA obtenido: {service.__class__.__name__}")
        print(f"[OK] Modelo configurado: {service.model_name}")
        
        # Probar una pregunta simple
        print("\n[TEST] Enviando mensaje de prueba...")
        mensaje = "Hola, soy un usuario nuevo. ¿Que materiales puedo reciclar?"
        
        # Simular datos del usuario
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Obtener el primer usuario o crear uno de prueba
        try:
            usuario = User.objects.first()
            if not usuario:
                print("[WARNING] No hay usuarios en la base de datos")
                print("[INFO] Creando usuario de prueba...")
                usuario = User.objects.create_user(
                    username='test_chatbot',
                    email='test@chatbot.com',
                    password='test123'
                )
                print(f"[OK] Usuario de prueba creado: {usuario.username}")
            else:
                print(f"[OK] Usuario de prueba: {usuario.username} (ID: {usuario.id})")
        except Exception as e:
            print(f"[ERROR] Error al obtener/crear usuario: {e}")
            return False
        
        # Crear conversación de prueba
        from core.models import ConversacionChatbot
        import uuid
        
        session_id = f"test_{uuid.uuid4().hex[:8]}"
        conversacion = ConversacionChatbot.objects.create(
            usuario=usuario,
            session_id=session_id
        )
        print(f"[OK] Conversación creada (ID: {conversacion.id}, Session: {session_id})")
        
        # Procesar mensaje (de forma síncrona para pruebas)
        import asyncio
        
        async def test_async():
            respuesta, confidence = await service.process_message(
                user=usuario,
                mensaje=mensaje,
                conversacion_id=conversacion.id,
                include_history=False
            )
            return respuesta, confidence
        
        # Ejecutar la prueba asíncrona
        print("\n[PROCESSING] Esperando respuesta de Gemini...")
        respuesta, confidence = asyncio.run(test_async())
        
        print("\n" + "=" * 70)
        print("RESPUESTA DEL CHATBOT:")
        print("=" * 70)
        print(respuesta)
        print("=" * 70)
        print(f"\n[CONFIDENCE] Nivel de confianza: {confidence:.2%}")
        
        print("\n[SUCCESS] El chatbot funciona correctamente!")
        print("\n[INFO] Ahora puedes probar el chatbot en:")
        print("  - Mini Chat: http://localhost:8000/ (botón flotante)")
        print("  - Chat Completo: http://localhost:8000/chatbot/")
        
        # Limpiar conversación de prueba
        conversacion.delete()
        print("\n[CLEANUP] Conversación de prueba eliminada")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chatbot()
    sys.exit(0 if success else 1)
