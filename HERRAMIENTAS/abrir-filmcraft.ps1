param(
  [Parameter(Mandatory = $true)]
  [string]$Proyecto,

  [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

# Cargar configuración dinámica
$configFile = Join-Path $PSScriptRoot "config.local.json"
$Gui = ""
$Cli = ""
$Port = 8765

if (Test-Path $configFile) {
    try {
        $cfg = Get-Content $configFile -Raw | ConvertFrom-Json
        if ($cfg.filmcraft_gui -and (Test-Path $cfg.filmcraft_gui)) { $Gui = $cfg.filmcraft_gui }
        if ($cfg.filmcraft_cli -and (Test-Path $cfg.filmcraft_cli)) { $Cli = $cfg.filmcraft_cli }
        if ($cfg.port_bridge) { $Port = [int]$cfg.port_bridge }
    } catch {}
}

# Fallbacks dinámicos
if (-not $Gui -or -not (Test-Path $Gui)) {
    $candGui = Join-Path $env:USERPROFILE ".gemini\antigravity\scratch\craft_tools\filmcraft\filmcraft-0.9.0-windows-x64-portable\filmcraft.exe"
    if (Test-Path $candGui) { $Gui = $candGui }
}
if (-not $Cli -or -not (Test-Path $Cli)) {
    $candCli = Join-Path $env:USERPROFILE ".gemini\antigravity\scratch\craft_tools\filmcraft\filmcraft-0.9.0-windows-x64-portable\filmcraft-cli.exe"
    if (Test-Path $candCli) { $Cli = $candCli }
}

if (-not (Test-Path -LiteralPath $Gui)) { throw "No existe FilmCraft GUI en: $Gui. Ejecuta .\HERRAMIENTAS\setup-entorno.ps1" }
if (-not (Test-Path -LiteralPath $Cli)) { throw "No existe filmcraft-cli en: $Cli. Ejecuta .\HERRAMIENTAS\setup-entorno.ps1" }

if (-not (Test-Path -LiteralPath $Proyecto)) {
    $candidatos = @(
        (Join-Path $Root $Proyecto),
        (Join-Path $Root "PROYECTOS\$Proyecto")
    )
    $hallado = $candidatos | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

    if (-not $hallado) {
        $proyectosDir = Join-Path $Root "PROYECTOS"
        if (Test-Path $proyectosDir) {
            $match = Get-ChildItem -LiteralPath $proyectosDir -Directory |
                Where-Object { $_.Name -like "*$Proyecto*" } | Select-Object -First 1
            if ($match) { $hallado = $match.FullName }
        }
    }

    if ($hallado) { $Proyecto = $hallado }
}

# Acepta una carpeta de proyecto o un archivo .fcproj
if (Test-Path -LiteralPath $Proyecto -PathType Container) {
    $filmcraftDir = Join-Path $Proyecto "02_filmcraft"
    if (-not (Test-Path -LiteralPath $filmcraftDir)) {
        throw "La carpeta no tiene 02_filmcraft: $Proyecto"
    }
    
    # Ordenar por número de versión semántica _v(\d+) en vez de solo fecha de modificación
    $candidatos = Get-ChildItem -LiteralPath $filmcraftDir -Filter "*.fcproj" -File |
        Where-Object { $_.DirectoryName -notmatch "Auto-Save" }
    
    $fcproj = $candidatos | Sort-Object {
        if ($_.BaseName -match '_v(\d+)') { [int]$matches[1] } else { 0 }
    }, LastWriteTime -Descending | Select-Object -First 1

    if (-not $fcproj) {
        throw "No hay ningun .fcproj en: $filmcraftDir"
    }
    $Proyecto = $fcproj.FullName
} else {
    $Proyecto = (Resolve-Path -LiteralPath $Proyecto).Path
}

if (-not (Test-Path -LiteralPath $Proyecto)) {
    throw "No existe el proyecto: $Proyecto"
}

$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue

if ($listener) {
    $estado = & $Cli --bridge "127.0.0.1:$Port" inspect project --compact 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "FilmCraft esta abierto, pero el puente no responde en el puerto $Port."
    }

    & $Cli --bridge "127.0.0.1:$Port" exec file.save | Out-Null
    & $Cli --bridge "127.0.0.1:$Port" exec file.open "path=$Proyecto" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo abrir el proyecto en FilmCraft."
    }

    Write-Host "Proyecto abierto en FilmCraft via Bridge ($Port):" -ForegroundColor Green
    Write-Host "  $Proyecto"
    exit 0
}

# Manejo seguro de procesos existentes sin forzar Stop-Process destructivo
$abiertos = Get-Process -Name "filmcraft" -ErrorAction SilentlyContinue
if ($abiertos) {
    if ($NonInteractive) {
        throw "FilmCraft ya esta ejecutandose pero no escucha en el puerto $Port. En modo No-Interactivo no se forzara el cierre."
    } else {
        Write-Warning "Se detecto un proceso FilmCraft activo que no responde en el puerto $Port."
        $resp = Read-Host "¿Deseas cerrar el proceso FilmCraft anterior para reabrirlo con control remoto? (S/N)"
        if ($resp -match "^[sSyY]") {
            Stop-Process -Name "filmcraft" -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
        } else {
            Write-Host "Operacion cancelada por el usuario. Guarda tu trabajo manualmente en FilmCraft." -ForegroundColor Yellow
            exit 1
        }
    }
}

$cmdLine = "`"$Gui`" --control $Port --no-recover `"$Proyecto`""
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = $cmdLine
    CurrentDirectory = (Split-Path -Parent $Gui)
} | Out-Null

for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
        break
    }
}

if (-not (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)) {
    throw "FilmCraft no abrio el puerto de control $Port tras 20 segundos de espera."
}

Write-Host "FilmCraft abierto exitosamente con el proyecto:" -ForegroundColor Green
Write-Host "  $Proyecto"
Write-Host ""
Write-Host "Deja FilmCraft abierto mientras Antigravity edita en vivo." -ForegroundColor Yellow
