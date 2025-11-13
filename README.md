# 🌱 EcoPuntos 1.0 - Sistema de Gestión de Reciclaje

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Chatbot](https://img.shields.io/badge/Chatbot-Gemini%202.5%20Flash-brightgreen.svg)

Sistema web moderno para la gestión de puntos de reciclaje, canjes de materiales y recompensas ecológicas con **Chatbot IA integrado**. Permite a los usuarios registrar materiales reciclables, acumular puntos y canjearlos por recompensas.

## 🚀 Características Principales

### ✅ Funcionalidades Implementadas
- **Gestión de Usuarios**: Registro, autenticación y perfiles personalizados
- **Sistema de Puntos**: Acumulación inteligente de puntos por reciclaje
- **Canjes**: Intercambio de materiales por puntos verificados
- **Recompensas**: Sistema completo de recompensas canjeables
- **🤖 Chatbot IA**: Asistente inteligente con Google Gemini 2.5 Flash
- **Rutas de Recolección**: Gestión automatizada de rutas para recolectores
- **Notificaciones**: Sistema de alertas en tiempo real
- **Juegos Educativos**: Gamificación del proceso de reciclaje
- **Dashboard Avanzado**: Estadísticas y seguimiento detallado
- **Sistema de Niveles**: Progresión por engagement ecológico
- **API REST**: Endpoints completos para integración móvil

### 🤖 Chatbot IA - Nueva Funcionalidad
- **Google Gemini 2.5 Flash**: IA de última generación
- **Soporte en tiempo real**: WebSocket para comunicación instantánea
- **Información precisa**: Datos reales del usuario y proyecto
- **Escalamiento inteligente**: Derivación automática a soporte humano
- **Interfaz optimizada**: Diseño full-screen y responsive

## 🛠️ Tecnologías

### Backend
- **Django 4.2.7**: Framework web principal
- **Python 3.13+**: Lenguaje de programación
- **PostgreSQL**: Base de datos principal
- **Django REST Framework**: API REST
- **Django Channels**: WebSocket para tiempo real
- **Daphne**: Servidor ASGI

### Frontend
- **HTML5/CSS3**: Interfaz moderna
- **JavaScript ES6+**: Funcionalidades dinámicas
- **Bootstrap 5**: Framework CSS responsive
- **WebSocket API**: Comunicación en tiempo real

### IA y Servicios
- **Google Gemini 2.5 Flash**: Chatbot inteligente
- **Supabase**: Base de datos en la nube (opcional)
- **Email**: Sistema de notificaciones

## 🚀 Instalación y Configuración

### Prerrequisitos
```bash
Python 3.13+
PostgreSQL 13+
Node.js (para herramientas de desarrollo)
Git
```

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Felipe420-iu/ecopuntos1.0.git
cd ecopuntos1.0
```

### 2. Crear Entorno Virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Crear archivo `.env` basado en `.env.example`:
```bash
# Django
SECRET_KEY=tu-clave-secreta-muy-segura
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de Datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/ecopuntos

# Google Gemini IA (REQUERIDO para chatbot)
GOOGLE_API_KEY=tu-api-key-de-google-gemini

# Email (opcional)
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-de-aplicacion
```

### 5. Aplicar Migraciones
```bash
python manage.py migrate
```

### 6. Crear Superusuario
```bash
python manage.py createsuperuser
```

### 7. Cargar Datos Iniciales
```bash
python manage.py loaddata fixtures/materiales_iniciales.json
python manage.py loaddata fixtures/recompensas_iniciales.json
```

### 8. Ejecutar Servidor
```bash
python manage.py runserver
```

## 🎯 Uso del Chatbot IA

### Configuración de Google Gemini
1. Obtén una API key en [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Agrégala a tu archivo `.env`:
```bash
GOOGLE_API_KEY=AIzaSyABLn0ZrFeYnJk1515uzDEowc7px-xi1Zs
```
3. El chatbot estará disponible en `/chatbot/`

### Funcionalidades del Chatbot
- ✅ **Información del usuario**: Puntos, nivel, estadísticas
- ✅ **Consultas sobre materiales**: Tipos aceptados, puntos por kilo
- ✅ **Proceso de canjes**: Cómo funciona el sistema
- ✅ **Recompensas disponibles**: Catálogo completo
- ✅ **Soporte técnico**: Resolución de dudas
- ✅ **Escalamiento**: Derivación a soporte humano

## 📱 API REST

Endpoints principales disponibles:
```
GET /api/materiales/          # Lista materiales
GET /api/recompensas/         # Lista recompensas
POST /api/canjes/             # Crear canje
GET /api/user/profile/        # Perfil usuario
GET /api/notifications/       # Notificaciones
```

Documentación completa en `/api/docs/`

## 🧪 Testing

Ejecutar tests:
```bash
python manage.py test
```

Tests de diseño con Playwright:
```bash
npm install
npm run test:design
```

## 📊 Estructura del Proyecto

```
ecopuntos1.0/
├── core/                     # App principal
│   ├── chatbot/             # Sistema de chatbot IA
│   │   ├── consumers.py     # WebSocket consumers
│   │   └── services/        # Servicios de IA
│   ├── models.py            # Modelos de datos
│   ├── views.py             # Vistas principales
│   ├── urls.py              # URLs
│   └── templates/           # Templates HTML
├── api/                     # API REST
├── tests/                   # Tests automatizados
├── media/                   # Archivos subidos
├── staticfiles/             # Archivos estáticos
└── requirements.txt         # Dependencias
```

## 🔧 Configuración de Producción

### Variables de Entorno de Producción
```bash
DEBUG=False
SECRET_KEY=clave-super-secura-para-produccion
DATABASE_URL=postgresql://...
ALLOWED_HOSTS=tudominio.com
GOOGLE_API_KEY=tu-api-key-de-produccion
```

### Comandos de Deploy
```bash
python manage.py collectstatic
python manage.py migrate
gunicorn proyecto2023.asgi:application -k uvicorn.workers.UvicornWorker
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

- **Chatbot IA**: Disponible 24/7 en la plataforma
- **Email**: soporte@ecopuntos.com
- **Issues**: [GitHub Issues](https://github.com/Felipe420-iu/ecopuntos1.0/issues)

## 🎯 Roadmap

- [ ] App móvil nativa
- [ ] Integración con IoT (sensores de peso)
- [ ] Blockchain para trazabilidad
- [ ] Machine Learning para predicciones
- [ ] Integración con sistemas municipales

---

**EcoPuntos 1.0** - Haciendo el reciclaje más inteligente y accesible 🌱♻️