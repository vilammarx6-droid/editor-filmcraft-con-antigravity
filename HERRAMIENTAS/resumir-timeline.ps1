param(
    [Parameter(Mandatory = $true)]
    [string]$Proyecto
)

$ErrorActionPreference = "Stop"

$workspaceRoot = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path -LiteralPath $Proyecto)) {
    $candidatos = @(
        (Join-Path $workspaceRoot $Proyecto),
        (Join-Path $workspaceRoot "PROYECTOS\$Proyecto")
    )
    $hallado = $candidatos | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    
    if (-not $hallado) {
        # Búsqueda por coincidencia parcial en PROYECTOS
        $proyectosDir = Join-Path $workspaceRoot "PROYECTOS"
        if (Test-Path $proyectosDir) {
            $match = Get-ChildItem -LiteralPath $proyectosDir -Directory |
                Where-Object { $_.Name -like "*$Proyecto*" } | Select-Object -First 1
            if ($match) { $hallado = $match.FullName }
        }
    }

    if ($hallado) { $Proyecto = $hallado }
    else { throw "No se encontró el proyecto: $Proyecto" }
}

$fcDir = Join-Path $Proyecto "02_filmcraft"
if (-not (Test-Path -LiteralPath $fcDir)) {
    throw "La carpeta no tiene subdirectorio 02_filmcraft: $Proyecto"
}

# Ordenar por versión semántica _v(\d+)
$candidatos = Get-ChildItem -LiteralPath $fcDir -Filter "*.fcproj" -File |
    Where-Object { $_.DirectoryName -notmatch "Auto-Save" }

$fcproj = $candidatos | Sort-Object {
    if ($_.BaseName -match '_v(\d+)') { [int]$matches[1] } else { 0 }
}, LastWriteTime -Descending | Select-Object -First 1

if (-not $fcproj) {
    Write-Host "No hay ningún .fcproj todavía en $fcDir" -ForegroundColor Yellow
    exit 0
}

# Cargar ruta dinámica de filmcraft-cli
$configFile = Join-Path $PSScriptRoot "config.local.json"
$Cli = ""
$Port = 8765

if (Test-Path $configFile) {
    try {
        $cfg = Get-Content $configFile -Raw | ConvertFrom-Json
        if ($cfg.filmcraft_cli -and (Test-Path $cfg.filmcraft_cli)) { $Cli = $cfg.filmcraft_cli }
        if ($cfg.port_bridge) { $Port = [int]$cfg.port_bridge }
    } catch {}
}

if (-not $Cli -or -not (Test-Path $Cli)) {
    $candCli = Join-Path $env:USERPROFILE ".gemini\antigravity\scratch\craft_tools\filmcraft\filmcraft-0.9.0-windows-x64-portable\filmcraft-cli.exe"
    if (Test-Path $candCli) { $Cli = $candCli }
}

$TicksPerSec = 254016000000.0

if (-not (Test-Path -LiteralPath $Cli)) {
    throw "No existe filmcraft-cli.exe en: $Cli. Ejecuta .\HERRAMIENTAS\setup-entorno.ps1"
}

$tcp = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
$useBridge = $false

if ($tcp) {
    $projRaw = & $Cli --bridge "127.0.0.1:$Port" inspect project --compact 2>$null
    if ($LASTEXITCODE -eq 0 -and $projRaw) {
        $projJson = $projRaw | ConvertFrom-Json
        if ($projJson.path -eq $fcproj.FullName) {
            $useBridge = $true
        }
    }
}

if ($useBridge) {
    $seqRaw = & $Cli --bridge "127.0.0.1:$Port" inspect sequence --compact 2>$null
    $modo = "Puente en vivo (127.0.0.1:$Port)"
} else {
    $projRaw = & $Cli --project $fcproj.FullName inspect project --compact 2>$null
    $projJson = $projRaw | ConvertFrom-Json
    $seqRaw = & $Cli --project $fcproj.FullName inspect sequence --compact 2>$null
    $modo = "Headless (disco)"
}

$seqJson = $seqRaw | ConvertFrom-Json
$durSec = [math]::Round($seqJson.duration / $TicksPerSec, 2)

Write-Host "=== RESUMEN COMPACTO DE FILMCRAFT ($modo) ===" -ForegroundColor Cyan
Write-Host "Proyecto:  $($projJson.name) | Sin guardar (dirty): $($projJson.dirty) | Rev: $($projJson.revision)" -ForegroundColor Green
Write-Host "Archivo:   $($fcproj.Name)" -ForegroundColor Green
Write-Host "Secuencia: [id=$($seqJson.id)] $($seqJson.name) | $($seqJson.settings.width)x$($seqJson.settings.height) @ $($seqJson.settings.frame_rate.num)fps | Duración: ${durSec}s ($($seqJson.durationFrames) frames)" -ForegroundColor Green

Write-Host "`n--- Medios en Proyecto (Bins) ---" -ForegroundColor Yellow
foreach ($child in $projJson.root.children) {
    $cSec = [math]::Round($child.duration / $TicksPerSec, 2)
    Write-Host "  [item=$($child.item)] $($child.name) ($($child.type), ${cSec}s)"
}

Write-Host "`n--- Pistas de Video ---" -ForegroundColor Magenta
foreach ($v in $seqJson.video) {
    $count = $v.items.Count
    $transCount = $v.transitions.Count
    if ($count -gt 0) {
        $first = [math]::Round($v.items[0].start / $TicksPerSec, 2)
        $last  = [math]::Round($v.items[-1].end / $TicksPerSec, 2)
        Write-Host "  $($v.name) [id=$($v.id)]: $count clips (${first}s -> ${last}s), $transCount transiciones"
    } else {
        Write-Host "  $($v.name) [id=$($v.id)]: vacía" -ForegroundColor DarkGray
    }
}

Write-Host "`n--- Pistas de Audio ---" -ForegroundColor Cyan
foreach ($a in $seqJson.audio) {
    $count = $a.items.Count
    if ($count -gt 0) {
        $names = ($a.items | ForEach-Object { "$($_.name) [clip=$($_.clip)]" }) -join ", "
        Write-Host "  $($a.name) [id=$($a.id)]: $count clips -> $names"
    } else {
        Write-Host "  $($a.name) [id=$($a.id)]: vacía" -ForegroundColor DarkGray
    }
}
