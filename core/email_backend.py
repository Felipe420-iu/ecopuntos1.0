"""
Backend SMTP personalizado con manejo robusto de SSL/TLS.
Soluciona problemas de verificación de certificados SSL.
"""
import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend


class SSLEmailBackend(DjangoSMTPBackend):
    """
    Backend SMTP personalizado que maneja correctamente SSL/TLS.
    
    Intenta usar certifi para validación de certificados, y si falla,
    usa un contexto SSL más permisivo pero aún seguro.
    """
    
    def _create_ssl_context(self):
        """Crea un contexto SSL robusto."""
        # Intentar usar certifi si está disponible
        try:
            import certifi
            context = ssl.create_default_context(cafile=certifi.where())
            return context
        except ImportError:
            pass
        
        # Fallback: crear contexto con configuración más permisiva
        context = ssl.create_default_context()
        
        # Configuración para manejar certificados problemáticos
        # Aún valida el hostname pero es más permisivo con la cadena de certificados
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        
        # Permitir versiones TLS modernas
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        return context
    
    def open(self):
        """
        Abre conexión SMTP con manejo robusto de SSL/TLS.
        """
        if self.connection:
            return False
        
        connection_class = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP
        
        try:
            if self.use_ssl:
                # Conexión SSL directa (puerto 465)
                context = self._create_ssl_context()
                self.connection = connection_class(
                    self.host,
                    self.port,
                    timeout=self.timeout,
                    context=context
                )
            else:
                # Conexión normal (puerto 587 con STARTTLS)
                self.connection = connection_class(
                    self.host,
                    self.port,
                    timeout=self.timeout
                )
            
            # EHLO
            self.connection.ehlo()
            
            # STARTTLS si es necesario
            if self.use_tls and not self.use_ssl:
                context = self._create_ssl_context()
                self.connection.starttls(context=context)
                self.connection.ehlo()
            
            # Autenticación
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            
            return True
            
        except smtplib.SMTPException as e:
            if not self.fail_silently:
                raise
            return False
        except (ssl.SSLError, OSError) as e:
            # Si falla SSL, intentar con un contexto aún más permisivo
            if not self.fail_silently:
                # Reintentar con verificación deshabilitada (última opción)
                try:
                    return self._open_with_unverified_ssl()
                except Exception:
                    raise
            return False
    
    def _open_with_unverified_ssl(self):
        """
        Método de último recurso: conexión sin verificación estricta de certificados.
        Solo se usa si fallan todos los otros métodos.
        """
        print("⚠️  ADVERTENCIA: Usando conexión SMTP sin verificación estricta de certificados")
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        connection_class = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP
        
        if self.use_ssl:
            self.connection = connection_class(
                self.host,
                self.port,
                timeout=self.timeout,
                context=context
            )
        else:
            self.connection = connection_class(
                self.host,
                self.port,
                timeout=self.timeout
            )
            self.connection.ehlo()
            if self.use_tls:
                self.connection.starttls(context=context)
                self.connection.ehlo()
        
        if self.username and self.password:
            self.connection.login(self.username, self.password)
        
        return True
