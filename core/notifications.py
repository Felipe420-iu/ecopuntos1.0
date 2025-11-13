"""
Sistema de notificaciones por email para Eco Puntos
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Usuario, Canje
import logging

logger = logging.getLogger(__name__)

class NotificacionEmail:
    """Clase para manejar notificaciones por email"""
    
    @staticmethod
    def enviar_email_html(usuario, asunto, template_name, contexto):
        """
        Envía un email HTML usando un template
        """
        try:
            if not usuario.notificaciones_email:
                logger.info(f"Usuario {usuario.username} tiene notificaciones deshabilitadas")
                return False
                
            # Renderizar template HTML
            html_message = render_to_string(f'emails/{template_name}.html', contexto)
            plain_message = strip_tags(html_message)
            
            # Enviar email
            send_mail(
                subject=asunto,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[usuario.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Email enviado exitosamente a {usuario.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email a {usuario.email}: {str(e)}")
            return False

    @staticmethod
    def notificar_canje_solicitado(canje):
        """Notifica cuando se solicita un nuevo canje"""
        contexto = {
            'usuario': canje.usuario,
            'canje': canje,
            'material': canje.material.nombre,
            'peso': canje.peso,
            'puntos_estimados': canje.peso * canje.material.precio_por_kg,
        }
        
        asunto = f"Canje #{canje.id} - Solicitud recibida"
        
        return NotificacionEmail.enviar_email_html(
            usuario=canje.usuario,
            asunto=asunto,
            template_name='canje_solicitado',
            contexto=contexto
        )

    @staticmethod
    def notificar_canje_aprobado(canje):
        """Notifica cuando un canje es aprobado"""
        contexto = {
            'usuario': canje.usuario,
            'canje': canje,
            'material': canje.material.nombre,
            'peso': canje.peso,
            'puntos': canje.puntos,
        }
        
        asunto = f"¡Canje #{canje.id} Aprobado! - {canje.puntos} puntos ganados"
        
        return NotificacionEmail.enviar_email_html(
            usuario=canje.usuario,
            asunto=asunto,
            template_name='canje_aprobado',
            contexto=contexto
        )

    @staticmethod
    def notificar_canje_rechazado(canje, motivo=""):
        """Notifica cuando un canje es rechazado"""
        contexto = {
            'usuario': canje.usuario,
            'canje': canje,
            'material': canje.material.nombre,
            'motivo': motivo,
        }
        
        asunto = f"Canje #{canje.id} - Información importante"
        
        return NotificacionEmail.enviar_email_html(
            usuario=canje.usuario,
            asunto=asunto,
            template_name='canje_rechazado',
            contexto=contexto
        )

    @staticmethod
    def notificar_canje_en_revision(canje):
        """Notifica cuando un canje está en revisión"""
        contexto = {
            'usuario': canje.usuario,
            'canje': canje,
            'material': canje.material.nombre,
        }
        
        asunto = f"Canje #{canje.id} - En revisión"
        
        return NotificacionEmail.enviar_email_html(
            usuario=canje.usuario,
            asunto=asunto,
            template_name='canje_en_revision',
            contexto=contexto
        )

    @staticmethod
    def notificar_ruta_programada(ruta):
        """Notifica cuando se programa una ruta de recolección"""
        contexto = {
            'usuario': ruta.usuario,
            'ruta': ruta,
            'fecha': ruta.fecha_programada,
            'direccion': ruta.direccion,
        }
        
        asunto = f"Recolección programada - {ruta.fecha_programada.strftime('%d/%m/%Y')}"
        
        return NotificacionEmail.enviar_email_html(
            usuario=ruta.usuario,
            asunto=asunto,
            template_name='ruta_programada',
            contexto=contexto
        )

    @staticmethod
    def notificar_bienvenida(usuario):
        """Email de bienvenida para nuevos usuarios"""
        contexto = {
            'usuario': usuario,
        }
        
        asunto = "¡Bienvenido a Eco Puntos! 🌱"
        
        return NotificacionEmail.enviar_email_html(
            usuario=usuario,
            asunto=asunto,
            template_name='bienvenida',
            contexto=contexto
        )
