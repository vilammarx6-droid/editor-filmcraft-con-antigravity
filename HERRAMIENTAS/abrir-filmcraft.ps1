param(
  [Parameter(Mandatory = $true)]
  [string]$Proyecto
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Gui = "C:\Users\marx_\.gemini\antigravity\scratch\craft_tools\filmcraft\filmcraft-0.9.0-windows-x64-portable\filmcraft.exe"
$Cli = "C:\Users\marx_\.gemini\antigravity\scratch\craft_tools\filmcraft\filmcraft-0.9.0-windows-x64-portable\filmcraft-cli.exe"
$Port = 8765

if (-not (Test-Path -LiteralPath $Gui)) { throw "No existe FilmCraft: $Gui" }
if (-not (Test-Path -LiteralPath $Cli)) { throw "No existe filmcraft-cli: $Cli" }

if (-not (Test-Path -LiteralPath $Proyecto)) {
    $posible = Join-Path $Root $Proyecto
    if (Test-Path -LiteralPath $posible) {
        $Proyecto = $posible
    }
}

# Acepta una carpeta de proyecto o un archivo .fcproj
if (Test-Path -LiteralPath $Proyecto -PathType Container) {
    $filmcraftDir = Join-Path $Proyecto "02_filmcraft"
    if (-not (Test-Path -LiteralPath $filmcraftDir)) {
        throw "La carpeta no tiene 02_filmcraft: $Proyecto"
    }
    $fcproj = Get-ChildItem -LiteralPath $filmcraftDir -Filter "*.fcproj" -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
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

    Write-Host "Proyecto abierto en FilmCraft:" -ForegroundColor Green
    Write-Host "  $Proyecto"
    exit 0
}

$abiertos = Get-Process -Name "filmcraft" -ErrorAction SilentlyContinue
if ($abiertos) {
    Stop-Process -Name "filmcraft" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
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
    throw "FilmCraft no abrio el puerto de control $Port."
}

Write-Host "FilmCraft abierto con el proyecto:" -ForegroundColor Green
Write-Host "  $Proyecto"
Write-Host ""
Write-Host "Deja FilmCraft abierto mientras Antigravity edita en vivo." -ForegroundColor Yellow
