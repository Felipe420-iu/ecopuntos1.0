# Sistema de Rate Limiting (Throttling) - EcoPuntos

## 📋 Descripción General

Este sistema implementa **rate limiting** (limitación de tasa) para proteger la aplicación contra abuso, ataques DDoS, y uso excesivo de recursos. Utilizamos `django-ratelimit` para controlar la frecuencia de solicitudes por IP, usuario o combinación de ambos.

## 🎯 Objetivos

1. **Seguridad**: Prevenir ataques de fuerza bruta en login y registro
2. **Performance**: Proteger el servidor contra sobrecarga
3. **Costos**: Limitar llamadas a APIs de pago (OpenAI chatbot)
4. **Experiencia**: Garantizar disponibilidad para todos los usuarios

## ⚙️ Configuración

### Instalación

```bash
pip install django-ratelimit==4.1.0
```

### Settings (proyecto2023/settings.py)

```python
INSTALLED_APPS = [
    # ...
    'django_ratelimit',
    # ...
]

# Habilitar rate limiting (False para desactivar)
RATELIMIT_ENABLE = True

# Límites definidos por operación
RATELIMIT_RATES = {
    # Autenticación (muy restrictivos)
    'login': '5/m',              # 5 intentos por minuto
    'register': '3/h',           # 3 registros por hora
    'password_reset': '3/h',     # 3 resets por hora
    
    # Operaciones de usuario
    'canjes': '10/h',            # 10 canjes por hora
    'rutas': '20/h',             # 20 solicitudes de ruta por hora
    'dashboard': '60/m',         # 60 visitas al dashboard por minuto
    
    # Conductor
    'aprobar_canje': '30/h',     # 30 aprobaciones por hora
    'confirmar_ruta': '40/h',    # 40 confirmaciones por hora
    'reagendar_ruta': '20/h',    # 20 reagendamientos por hora
    
    # Chatbot (control de costos AI)
    'chatbot_message': '30/m',   # 30 mensajes por minuto
    'chatbot_session': '100/h',  # 100 sesiones por hora
    
    # Emails
    'send_email': '5/h',         # 5 emails por hora
    'contact_form': '3/h',       # 3 formularios por hora
    
    # APIs
    'api_general': '100/h',      # 100 llamadas API por hora
    'api_admin': '500/h',        # 500 llamadas admin por hora
    
    # Por rol (general)
    'user_general': '100/h',     # Usuarios normales
    'conductor_general': '200/h', # Conductores
    'admin_general': '500/h',    # Administradores
    'anonymous': '20/h',         # No autenticados
}

# Cache backend para rate limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'default-ratelimit',
        'OPTIONS': {
            'MAX_ENTRIES': 10000
        }
    }
}

# Vista personalizada para errores de rate limit
RATELIMIT_VIEW = 'core.views.ratelimit_error'
```

## 🔧 Uso en Vistas

### Decoradores Predefinidos

```python
from core.ratelimit import (
    ratelimit_login,
    ratelimit_register,
    ratelimit_canje,
    ratelimit_chatbot,
    smart_ratelimit
)

# Login (5 intentos por minuto)
@ratelimit_login
def iniciosesion(request):
    # ...

# Canjes (10 por hora)
@login_required
@ratelimit_canje
def canjes(request):
    # ...

# Chatbot (30 mensajes por minuto)
@login_required
@ratelimit_chatbot
def chatbot_view(request):
    # ...
```

### Decorador Inteligente (smart_ratelimit)

```python
# Se adapta automáticamente al rol del usuario
@login_required
@smart_ratelimit(key='user', rate='40/h', method='POST')
def confirmar_ruta(request, ruta_id):
    # Si no especificas 'rate', usa límites por rol:
    # - Admin: 500/h
    # - Conductor: 200/h
    # - Usuario: 100/h
    # - Anónimo: 20/h
```

### Parámetros del Decorador

- **key**: Identificador único
  - `'ip'`: Limitar por dirección IP
  - `'user'`: Limitar por usuario autenticado
  - `'user_or_ip'`: Combinar ambos
  
- **rate**: Límite de solicitudes
  - `'5/m'`: 5 por minuto
  - `'100/h'`: 100 por hora
  - `'1000/d'`: 1000 por día
  
- **method**: Métodos HTTP a limitar
  - `'POST'`: Solo POST
  - `'GET'`: Solo GET
  - `'ALL'`: Todos los métodos
  
- **block**: Si True, bloquea cuando se excede (default: True)

## 📊 Límites Implementados

### Por Vista

| Vista | Límite | Razón |
|-------|--------|-------|
| `iniciosesion` | 5/minuto | Prevenir fuerza bruta |
| `canjes` | 10/hora | Evitar spam de canjes |
| `confirmar_ruta` | 40/hora | Control conductor |
| `aprobar_canje_peso_real` | 30/hora | Control aprobaciones |
| `chatbot_view` | 60/minuto | Acceso a interfaz |

### Por Rol

| Rol | Límite General |
|-----|----------------|
| Anónimo | 20/hora |
| Usuario | 100/hora |
| Conductor | 200/hora |
| Admin | 500/hora |

## 🎨 Experiencia de Usuario

### Respuesta AJAX

Cuando se excede el límite en una petición AJAX:

```json
{
    "success": false,
    "error": "Límite de solicitudes excedido",
    "message": "Has realizado demasiadas solicitudes. Por favor, intenta más tarde.",
    "retry_after": 60,
    "type": "rate_limit"
}
```

### Página HTML

Cuando se excede en una petición normal:
- Redirige a `core/ratelimit_error.html`
- Muestra cuenta regresiva visual (60 segundos)
- Diseño amigable con animaciones
- Botón para volver se habilita después del countdown

## 🧪 Testing

### Probar Límites Manualmente

```python
# En shell de Django
python manage.py shell

from django.test import Client
from django.contrib.auth import get_user_model

client = Client()
User = get_user_model()

# Probar login (5 intentos por minuto)
for i in range(6):
    response = client.post('/iniciosesion/', {
        'username': 'test',
        'password': 'wrong'
    })
    print(f"Intento {i+1}: {response.status_code}")
    # El 6to debe devolver 429 (Too Many Requests)
```

### Verificar Configuración

```bash
# Ver configuración actual
python manage.py shell
>>> from django.conf import settings
>>> settings.RATELIMIT_ENABLE
True
>>> settings.RATELIMIT_RATES['login']
'5/m'
```

## 🚀 Despliegue

### Desarrollo

Cache en memoria (LocMemCache) está bien para desarrollo.

### Producción

Cambiar a Redis para mejor performance:

```python
# settings.py (producción)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

Instalar Redis:
```bash
pip install django-redis redis
```

## 📝 Mantenimiento

### Desactivar Temporalmente

```python
# settings.py
RATELIMIT_ENABLE = False  # Desactiva todos los límites
```

### Ajustar Límites

Editar `RATELIMIT_RATES` en settings.py y reiniciar servidor.

### Monitorear

Ver logs de rate limiting:
```bash
# Buscar en logs
grep "rate limit" logs/django.log
```

## 🔐 Seguridad

- Los límites se aplican **antes** de la autenticación (para login)
- Se usa IP real considerando proxies (X-Forwarded-For)
- Los usuarios autenticados tienen límites más generosos
- Los admins tienen límites mucho más altos

## 📚 Referencias

- [django-ratelimit docs](https://django-ratelimit.readthedocs.io/)
- [HTTP 429 Status](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429)
- [Rate Limiting Patterns](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)

## 🐛 Troubleshooting

### Error: "No module named 'django_ratelimit'"
```bash
pip install django-ratelimit
```

### Error: "Cannot import name 'ratelimit_login'"
Verificar que `core/ratelimit.py` existe y tiene los decoradores.

### Los límites no se aplican
1. Verificar `RATELIMIT_ENABLE = True` en settings.py
2. Verificar que el decorador esté aplicado a la vista
3. Reiniciar servidor

### Cache no funciona
1. Verificar configuración de CACHES en settings.py
2. Para producción, usar Redis en lugar de LocMemCache

---

**Implementado por**: EcoPuntos Team  
**Fecha**: 2024  
**Versión**: 1.0
