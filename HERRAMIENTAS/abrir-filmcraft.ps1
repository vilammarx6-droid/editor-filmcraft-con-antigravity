param(
  [Parameter(Mandatory = $true)]
  [string]$Proyecto
)

$ErrorActionPreference = "Stop"

$Gui = "C:\Users\marx_\.gemini\antigravity\scratch\craft_tools\filmcraft\filmcraft-0.9.0-windows-x64-portable\filmcraft.exe"
$Cli = "C:\Users\marx_\.gemini\antigravity\scratch\craft_tools\filmcraft\filmcraft-0.9.0-windows-x64-portable\filmcraft-cli.exe"
$Port = 8765

if (-not (Test-Path -LiteralPath $Gui)) { throw "No existe FilmCraft: $Gui" }
if (-not (Test-Path -LiteralPath $Cli)) { throw "No existe filmcraft-cli: $Cli" }

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
        throw "No hay ningún .fcproj en: $filmcraftDir"
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
        throw "FilmCraft está abierto, pero el puente no responde en el puerto $Port."
    }

    $info = $estado | ConvertFrom-Json
    if ($info.dirty) {
        throw "FilmCraft tiene cambios sin guardar. Guarda el proyecto actual antes de abrir otro."
    }

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
    throw "FilmCraft ya está abierto, pero sin control en el puerto $Port. Ciérralo y vuelve a ejecutar este script."
}

Start-Process -FilePath $Gui -ArgumentList @(
    "--control", "$Port", "--no-recover", "`"$Proyecto`""
) -WorkingDirectory (Split-Path -Parent $Gui)

for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
        break
    }
}

if (-not (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)) {
    throw "FilmCraft no abrió el puerto de control $Port."
}

Write-Host "FilmCraft abierto con el proyecto:" -ForegroundColor Green
Write-Host "  $Proyecto"
Write-Host ""
Write-Host "Deja FilmCraft abierto mientras Antigravity edita." -ForegroundColor Yellow
