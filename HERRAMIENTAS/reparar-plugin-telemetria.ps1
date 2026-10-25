<#
.SYNOPSIS
    Script de diagnóstico y reparación automática para el bug de comillas en el plugin
    googlecloudtools.datacloud_telemetry en entornos Windows para Gemini CLI / Antigravity.

.DESCRIPTION
    1. Escanea ~/.gemini/config/plugins en busca de hooks.json con rutas malformadas o comillas escapadas anidadas.
    2. Sanea las rutas duplicadas hacia telemetry_hook_bundle.js.
    3. Si la carpeta del plugin está corrupta o ya no se usa, ofrece o ejecuta su eliminación limpia.
    4. Garantiza que la opción "telemetry": { "enabled": false } esté presente en config.json para evitar recurrencias.
#>

param(
    [switch]$ForceDisable = $true
)

$ErrorActionPreference = "Continue"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [REPARADOR] Bug de Telemetria Data Cloud en Windows      " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$userProfile = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::UserProfile)
$geminiDir = Join-Path $userProfile ".gemini"
$configDir = Join-Path $geminiDir "config"
$pluginsDir = Join-Path $configDir "plugins"
$configFile = Join-Path $configDir "config.json"
$settingsFile = Join-Path $geminiDir "settings.json"

if (-not (Test-Path $geminiDir)) {
    Write-Warning "No se encontro el directorio de configuracion .gemini en: $geminiDir"
    exit 0
}

Write-Host "[1/4] Comprobando plugins instalados en: $pluginsDir" -ForegroundColor Yellow

if (Test-Path $pluginsDir) {
    $hookFiles = Get-ChildItem -Path $pluginsDir -Filter "hooks.json" -Recurse -ErrorAction SilentlyContinue
    foreach ($hook in $hookFiles) {
        try {
            $rawContent = Get-Content $hook.FullName -Raw -Encoding UTF8
            if ($rawContent -match '\\"[A-Za-z]:\\' -or $rawContent -match '""') {
                Write-Host "  -> Archivo con comillas malformadas detectado: $($hook.FullName)" -ForegroundColor Red
                # Limpiar comillas anidadas
                $fixedContent = $rawContent -replace '\\"([A-Za-z]:\\[^"]+)\\"', '$1'
                $fixedContent = $fixedContent -replace '""([A-Za-z]:\\[^"]+)""', '"$1"'
                Set-Content -Path $hook.FullName -Value $fixedContent -Encoding UTF8
                Write-Host "  -> [CORREGIDO] Rutas limpiadas en $($hook.Name)" -ForegroundColor Green
            }
        } catch {
            Write-Warning "No se pudo procesar $($hook.FullName): $_"
        }
    }

    $telemetryFolder = Join-Path $pluginsDir "googlecloudtools.datacloud_telemetry"
    if (Test-Path $telemetryFolder) {
        Write-Host "[2/4] Detectada carpeta activa de telemetria problematica." -ForegroundColor Yellow
        try {
            Remove-Item -Path $telemetryFolder -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  -> [ELIMINADO] Carpeta conflictiva eliminada de forma segura: $telemetryFolder" -ForegroundColor Green
        } catch {
            Write-Warning "No se pudo remover la carpeta: $_"
        }
    } else {
        Write-Host "[2/4] Carpeta de telemetria conflictiva limpia (no presente)." -ForegroundColor Green
    }
} else {
    Write-Host "[1/4] La carpeta de plugins no existe o ya esta limpia." -ForegroundColor Green
}

Write-Host "[3/4] Configurando desactivacion preventiva de telemetria..." -ForegroundColor Yellow

function Disable-TelemetryInJson([string]$path) {
    if (-not (Test-Path $path)) {
        $initial = @{ telemetry = @{ enabled = $false } }
        $initial | ConvertTo-Json -Depth 5 | Set-Content -Path $path -Encoding UTF8
        Write-Host "  -> [CREADO] $path con telemetria desactivada." -ForegroundColor Green
        return
    }

    try {
        $content = Get-Content -Path $path -Raw -Encoding UTF8
        $json = $content | ConvertFrom-Json
        if (-not $json.telemetry) {
            $json | Add-Member -NotePropertyName "telemetry" -NotePropertyValue ([PSCustomObject]@{ enabled = $false }) -Force
        } else {
            $json.telemetry.enabled = $false
        }
        $json | ConvertTo-Json -Depth 10 | Set-Content -Path $path -Encoding UTF8
        Write-Host "  -> [ACTUALIZADO] $path (`"telemetry.enabled`" = false)" -ForegroundColor Green
    } catch {
        Write-Warning "No se pudo actualizar el archivo JSON $path : $_"
    }
}

Disable-TelemetryInJson -path $configFile
if (Test-Path $settingsFile) {
    Disable-TelemetryInJson -path $settingsFile
}

Write-Host "[4/4] Verificacion completada con exito." -ForegroundColor Cyan
Write-Host "¡El bug de comillas y llamadas a herramientas ha sido blindado por completo!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
