# deploy.ps1 — Despliega gym-tracker en omvdls
# Ejecutar desde la carpeta gym-tracker/ cuando el servidor este accesible
#
# Uso: .\deploy.ps1
# Requiere: OpenSSH en Windows (viene con Windows 10/11)

$SERVER_HOST = "192.168.0.23"
$SERVER_PORT = "2222"
$SERVER_USER = "root"
$SSH_KEY     = "$env:USERPROFILE\.ssh\id_ed25519"
$REMOTE_DIR  = "/var/lib/casaos/apps/gym-tracker"
$LOCAL_DIR   = $PSScriptRoot

$SSH = "ssh -i `"$SSH_KEY`" -p $SERVER_PORT -o StrictHostKeyChecking=no"
$SCP = "scp -i `"$SSH_KEY`" -P $SERVER_PORT -o StrictHostKeyChecking=no"

Write-Host "=== gym-tracker deploy ===" -ForegroundColor Cyan
Write-Host "Servidor: $SERVER_USER@${SERVER_HOST}:$SERVER_PORT" -ForegroundColor Gray
Write-Host ""

# 1. Crear directorio en servidor
Write-Host "[1/3] Creando directorio remoto..." -ForegroundColor Yellow
Invoke-Expression "$SSH ${SERVER_USER}@${SERVER_HOST} 'mkdir -p $REMOTE_DIR'"

# 2. Copiar archivos
Write-Host "[2/3] Subiendo archivos..." -ForegroundColor Yellow
$files = @("index.html","gym-dia1.html","gym-dia2.html","gym-dia3.html","docker-compose.yml")
foreach ($f in $files) {
    Write-Host "  Subiendo $f..."
    Invoke-Expression "$SCP `"$LOCAL_DIR\$f`" ${SERVER_USER}@${SERVER_HOST}:$REMOTE_DIR/"
}

# 3. Arrancar contenedor
Write-Host "[3/3] Arrancando contenedor..." -ForegroundColor Yellow
Invoke-Expression "$SSH ${SERVER_USER}@${SERVER_HOST} 'cd $REMOTE_DIR && docker compose up -d'"

Write-Host ""
Write-Host "=== Listo ===" -ForegroundColor Green
Write-Host "Web disponible en: http://${SERVER_HOST}:8095" -ForegroundColor Cyan
Write-Host "Via Tailscale:     http://100.72.238.89:8095" -ForegroundColor Cyan
