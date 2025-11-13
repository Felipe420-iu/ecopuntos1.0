# Script de limpieza para EcoPuntos - Eliminar archivos basura
# Ejecutar desde el directorio raíz del proyecto

Write-Host "🧹 INICIANDO LIMPIEZA DE ARCHIVOS BASURA..." -ForegroundColor Yellow
Write-Host "=" * 60

# 1. Eliminar archivos .pyc (cache Python) - 5.3 MB
Write-Host "🗑️  Eliminando archivos .pyc..." -ForegroundColor Cyan
Get-ChildItem -Recurse -Include "*.pyc" | Remove-Item -Force -Verbose
Get-ChildItem -Recurse -Name "__pycache__" -Directory | Remove-Item -Recurse -Force -Verbose

# 2. Eliminar archivos temporales
Write-Host "🗑️  Eliminando archivos temporales..." -ForegroundColor Cyan
Remove-Item "~WRL*.tmp" -Force -ErrorAction SilentlyContinue
Remove-Item "test-results/.last-run.json" -Force -ErrorAction SilentlyContinue

# 3. Limpiar logs gigantes (mantener estructura pero vaciar)
Write-Host "🗑️  Limpiando logs..." -ForegroundColor Cyan
Clear-Content "logs/ecopuntos.log" -Force -ErrorAction SilentlyContinue

# 4. Eliminar tests obsoletos
Write-Host "🗑️  Eliminando tests obsoletos..." -ForegroundColor Cyan
$obsoleteTests = @(
    "test_chat_direct.py",
    "test_email.py", 
    "test_debug_modal.py",
    "test_correo_reagendamiento.py",
    "test_modal_automatico.py",
    "test_modal_final.py",
    "test_final_modal.py"
)
foreach ($test in $obsoleteTests) {
    Remove-Item $test -Force -ErrorAction SilentlyContinue -Verbose
}

# 5. Eliminar scripts de debug/diagnóstico temporales
Write-Host "🗑️  Eliminando scripts de debug..." -ForegroundColor Cyan
$debugScripts = @(
    "debug_modal.py",
    "diagnostico_chatbot.py", 
    "diagnostico_correos.py",
    "demo_reagendamiento.py",
    "crear_demo_reagendamiento.py"
)
foreach ($script in $debugScripts) {
    Remove-Item $script -Force -ErrorAction SilentlyContinue -Verbose
}

# 6. Eliminar scripts de setup una vez
Write-Host "🗑️  Eliminando scripts de setup temporales..." -ForegroundColor Cyan
$setupScripts = @(
    "actualizar_terminos_usuarios.py",
    "check_recompensas.py",
    "check_setup.py", 
    "populate_recompensas.py",
    "export_users.py",
    "import_users.py",
    "generar_notificaciones_test.py"
)
foreach ($script in $setupScripts) {
    Remove-Item $script -Force -ErrorAction SilentlyContinue -Verbose
}

# 7. Eliminar backups temporales
Write-Host "🗑️  Eliminando backups temporales..." -ForegroundColor Cyan
Remove-Item "usuarios_backup.json" -Force -ErrorAction SilentlyContinue -Verbose

# 8. Eliminar directorios vacíos
Write-Host "🗑️  Eliminando directorios vacíos..." -ForegroundColor Cyan
Remove-Item "data/chromadb" -Recurse -Force -ErrorAction SilentlyContinue -Verbose

Write-Host ""
Write-Host "✅ LIMPIEZA COMPLETADA!" -ForegroundColor Green
Write-Host "📊 Espacio liberado aproximado: ~20-25 MB" -ForegroundColor Green
Write-Host "🗂️  Archivos eliminados: ~30+ archivos basura" -ForegroundColor Green