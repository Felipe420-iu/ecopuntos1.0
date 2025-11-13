import smtplib
import ssl
import certifi

from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend


class CertifiSMTPBackend(DjangoSMTPBackend):
    """Custom SMTP backend that uses certifi's CA bundle for TLS/SSL.

    This helps in environments where the system OpenSSL CA store is missing
    or contains certificates that fail strict verification. For production
    you should ensure the OS certificate store is correct instead of
    disabling/overriding validation.
    """

    def _create_ssl_context(self):
        """Create an SSLContext using certifi's CA bundle."""
        context = ssl.create_default_context(cafile=certifi.where())
        return context

    def open(self):
        """Open a network connection and optionally start TLS with certifi context."""
        if self.connection:
            return False

        try:
            if self.use_ssl:
                context = self._create_ssl_context()
                connection = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout, context=context)
            else:
                connection = smtplib.SMTP(self.host, self.port, timeout=self.timeout)

            connection.ehlo()

            if not self.use_ssl and self.use_tls:
                # Start TLS with certifi-backed context
                context = self._create_ssl_context()
                connection.starttls(context=context)
                connection.ehlo()

            if self.username and self.password:
                connection.login(self.username, self.password)

            self.connection = connection
            return True

        except Exception:
            if not self.fail_silently:
                raise
            return False
