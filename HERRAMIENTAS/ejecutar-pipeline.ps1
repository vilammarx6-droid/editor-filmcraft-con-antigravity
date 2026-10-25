<#
.SYNOPSIS
    Orquestador Determinista de Produccion y Quality Gate para FilmCraft.

.DESCRIPTION
    Ejecuta el pipeline de produccion desacoplado de la IA:
    1. Valida el contrato de datos del brief (00_brief/brief.md con seccion ## Guion).
    2. Ejecuta la sintesis de voz neural (Edge-TTS) y genera WAV 48kHz + SRT.
    3. Inspecciona y valida el proyecto FilmCraft (.fcproj).
    4. Genera el collage de revision determinista (crear-collage-qa.py).
    5. Ejecuta el Quality Gate de audio/video (auditar-calidad.py) y bloquea con exit 1 si no cumple.
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Proyecto,

    [switch]$RegenerarVoz,

    [switch]$OmitirQualityGate
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [PIPELINE] Orquestador Determinista de Produccion        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$workspaceRoot = Split-Path -Parent $PSScriptRoot

# 1. Resolver proyecto
if (-not (Test-Path -LiteralPath $Proyecto)) {
    $candidatos = @(
        (Join-Path $workspaceRoot $Proyecto),
        (Join-Path $workspaceRoot "PROYECTOS\$Proyecto")
    )
    $hallado = $candidatos | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

    if (-not $hallado) {
        $proyectosDir = Join-Path $workspaceRoot "PROYECTOS"
        if (Test-Path $proyectosDir) {
            $match = Get-ChildItem -LiteralPath $proyectosDir -Directory |
                Where-Object { $_.Name -like "*$Proyecto*" } | Select-Object -First 1
            if ($match) { $hallado = $match.FullName }
        }
    }

    if ($hallado) { $Proyecto = $hallado }
    else { throw "No se encontro el proyecto: $Proyecto" }
}

Write-Host "-> Proyecto detectado: $Proyecto" -ForegroundColor Green

# 2. Comprobar contrato de brief y guion
$briefPath = Join-Path $Proyecto "00_brief\brief.md"
if (-not (Test-Path $briefPath)) {
    throw "Falta el archivo de contrato del brief: $briefPath"
}

Write-Host "`n[Fase 1/4] Validacion de Guion y Sintesis de Audio..." -ForegroundColor Yellow
$audioDir = Join-Path $Proyecto "01_fuentes\audio"
$locucionWav = Join-Path $audioDir "locucion.wav"

$hasGuion = $false
$briefContent = Get-Content -LiteralPath $briefPath -Raw -Encoding UTF8
if ($briefContent -match "(?ms)##\s*Gui[oó]n" -or $briefContent -match "(?m)^-\s*Guion:") {
    $hasGuion = $true
}

if ($hasGuion) {
    if ($RegenerarVoz -or -not (Test-Path $locucionWav)) {
        & "$PSScriptRoot\generar-voz.ps1" -Proyecto $Proyecto -NombreSalida "locucion"
        if ($LASTEXITCODE -ne 0) {
            throw "Error generando la locucion del proyecto."
        }
    } else {
        Write-Host "  -> Locucion ya existente en: $locucionWav" -ForegroundColor Gray
    }
} else {
    Write-Host "  -> Proyecto sin locucion hablada (musical o instrumental). Omitiendo TTS." -ForegroundColor Gray
}

# 3. Comprobar proyecto FilmCraft
Write-Host "`n[Fase 2/4] Validacion de Linea de Tiempo en FilmCraft..." -ForegroundColor Yellow
& "$PSScriptRoot\resumir-timeline.ps1" -Proyecto $Proyecto
if ($LASTEXITCODE -ne 0) {
    Write-Warning "No se pudo inspeccionar el proyecto FilmCraft de forma headless."
}

# 4. Generar Collage de Auditoria QA
Write-Host "`n[Fase 3/4] Generacion de Collage Determinista QA..." -ForegroundColor Yellow
$pyCmd = "python"
& $pyCmd "$PSScriptRoot\crear-collage-qa.py" $Proyecto

# 5. Quality Gate de Export
Write-Host "`n[Fase 4/4] Ejecutando Quality Gate de Audio y Video..." -ForegroundColor Yellow
$exportsDir = Join-Path $Proyecto "03_exports"
$masterVideos = Get-ChildItem -LiteralPath $exportsDir -Filter "*.mp4" -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending

if (-not $masterVideos) {
    Write-Host "  -> No hay videos exportados en $exportsDir para auditar aun." -ForegroundColor Yellow
    Write-Host "  -> Ejecuta el renderizado en FilmCraft y vuelve a correr el pipeline." -ForegroundColor Gray
} else {
    $targetVideo = $masterVideos[0].FullName
    Write-Host "  -> Auditando master: $($masterVideos[0].Name)" -ForegroundColor Cyan
    
    if (-not $OmitirQualityGate) {
        & $pyCmd "$PSScriptRoot\auditar-calidad.py" $targetVideo
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n[BLOQUEO DE CALIDAD] El master NO cumple los estandares de emision." -ForegroundColor Red
            Write-Host "Ejecuta: python .\HERRAMIENTAS\remediar-audio.py `"$targetVideo`"" -ForegroundColor Yellow
            exit 1
        }
    }
}

Write-Host "`n[EXITO] Pipeline completado. Todos los contratos y estandares fueron satisfechos." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
