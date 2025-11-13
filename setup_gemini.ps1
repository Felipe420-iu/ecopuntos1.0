# Script de Instalacion - Gemini 1.5 Flash
Write-Host ""
Write-Host "========================================"
Write-Host "  CONFIGURACION GEMINI 1.5 FLASH"
Write-Host "  EcoPuntos Chatbot IA"
Write-Host "========================================"
Write-Host ""

# Instalar dependencia
Write-Host "Paso 1: Instalando google-generativeai..."
pip install google-generativeai

if ($LASTEXITCODE -eq 0) {
    Write-Host "OK - Instalacion completada" -ForegroundColor Green
} else {
    Write-Host "ERROR - Fallo en instalacion" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================"
Write-Host "  INSTALACION COMPLETADA"
Write-Host "========================================"
Write-Host ""
Write-Host "Proximos pasos:"
Write-Host "1. Obtener API key GRATIS en:"
Write-Host "   https://makersuite.google.com/app/apikey"
Write-Host ""
Write-Host "2. Configurar en .env:"
Write-Host "   GOOGLE_API_KEY=tu_key_aqui"
Write-Host ""
Write-Host "3. Iniciar servidor:"
Write-Host "   python manage.py runserver"
Write-Host ""
Write-Host "Lee: CHATBOT_GEMINI_README.md para mas info"
Write-Host ""