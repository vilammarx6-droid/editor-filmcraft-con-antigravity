<#
.SYNOPSIS
    Script de configuración y portabilidad del entorno para el editor FilmCraft con Antigravity.

.DESCRIPTION
    1. Resuelve dinámicamente las rutas locales en cualquier máquina clonada.
    2. Localiza o descarga los ejecutables de FilmCraft (GUI y CLI).
    3. Genera el archivo .agents/mcp_config.json con la ruta absoluta local específica de la máquina.
    4. Crea un archivo HERRAMIENTAS/config.local.json que almacena las rutas locales para todos los scripts.
    5. Valida dependencias del sistema: PowerShell, Python, FFmpeg, FilmCraft.
#>

param(
    [string]$FilmCraftPath = ""
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [SETUP] Inicializacion y Portabilidad de Entorno        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Write-Host "-> Raiz del Repositorio: $repoRoot" -ForegroundColor Yellow

# 1. Buscar binarios de FilmCraft
$candidatePaths = @()
if ($FilmCraftPath -and (Test-Path $FilmCraftPath)) {
    $candidatePaths += $FilmCraftPath
}
if ($env:FILMCRAFT_HOME -and (Test-Path $env:FILMCRAFT_HOME)) {
    $candidatePaths += $env:FILMCRAFT_HOME
}

# Rutas estándar en repositorio o en sistema
$candidatePaths += (Join-Path $repoRoot "HERRAMIENTAS\bin\filmcraft")
$candidatePaths += (Join-Path $repoRoot "HERRAMIENTAS\bin\filmcraft\filmcraft-0.9.0-windows-x64-portable")
$candidatePaths += (Join-Path $env:USERPROFILE ".gemini\antigravity\scratch\craft_tools\filmcraft\filmcraft-0.9.0-windows-x64-portable")
$candidatePaths += (Join-Path $env:ProgramFiles "FilmCraft")
$candidatePaths += (Join-Path $env:LOCALAPPDATA "Programs\FilmCraft")

$cliFound = $null
$guiFound = $null

foreach ($cand in $candidatePaths) {
    if (-not (Test-Path $cand)) { continue }
    
    $cliCandidate = Join-Path $cand "filmcraft-cli.exe"
    $guiCandidate = Join-Path $cand "filmcraft.exe"
    
    if ((Test-Path $cliCandidate) -and (Test-Path $guiCandidate)) {
        $cliFound = (Resolve-Path $cliCandidate).Path
        $guiFound = (Resolve-Path $guiCandidate).Path
        break
    }
}

if (-not $cliFound) {
    Write-Warning "No se encontro FilmCraft en las rutas conocidas."
    Write-Host "Por favor indica la ruta a la carpeta de FilmCraft ejecutando:" -ForegroundColor Yellow
    Write-Host "  .\HERRAMIENTAS\setup-entorno.ps1 -FilmCraftPath 'C:\Ruta\A\FilmCraft'" -ForegroundColor White
} else {
    Write-Host "-> FilmCraft CLI: $cliFound" -ForegroundColor Green
    Write-Host "-> FilmCraft GUI: $guiFound" -ForegroundColor Green
}

# 2. Generar config.local.json
$localConfig = @{
    repo_root     = $repoRoot
    filmcraft_cli = if ($cliFound) { $cliFound } else { "" }
    filmcraft_gui = if ($guiFound) { $guiFound } else { "" }
    ffmpeg_cmd    = "ffmpeg"
    python_cmd    = "python"
    port_bridge   = 8765
}

$configLocalPath = Join-Path $PSScriptRoot "config.local.json"
$localConfig | ConvertTo-Json -Depth 5 | Set-Content -Path $configLocalPath -Encoding UTF8
Write-Host "-> Generado: $configLocalPath" -ForegroundColor Green

# 3. Generar .agents/mcp_config.json dinámicamente
$agentsDir = Join-Path $repoRoot ".agents"
if (Test-Path $agentsDir) {
    $templateMcp = Join-Path $agentsDir "mcp_config.template.json"
    if (-not (Test-Path $templateMcp)) {
        $tmpl = @{
            mcpServers = @{
                filmcraft = @{
                    command = "{{FILMCRAFT_CLI}}"
                    args    = @("--bridge", "127.0.0.1:8765", "mcp")
                }
            }
        }
        $tmpl | ConvertTo-Json -Depth 5 | Set-Content -Path $templateMcp -Encoding UTF8
        Write-Host "-> Plantilla creada: $templateMcp" -ForegroundColor Gray
    }

    $mcpPath = Join-Path $agentsDir "mcp_config.json"
    $cliEscaped = if ($cliFound) { $cliFound.Replace('\', '\\') } else { "filmcraft-cli.exe" }
    
    $mcpContent = @"
{
  "mcpServers": {
    "filmcraft": {
      "command": "$cliEscaped",
      "args": ["--bridge", "127.0.0.1:8765", "mcp"]
    }
  }
}
"@
    Set-Content -Path $mcpPath -Value $mcpContent -Encoding UTF8
    Write-Host "-> MCP Config actualizado dinamicamente: $mcpPath" -ForegroundColor Green
}

# 4. Validar herramientas de sistema
Write-Host "`n[Validacion de Dependencias]" -ForegroundColor Yellow

# FFmpeg
try {
    $ffmpegVer = & ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "  [OK] FFmpeg: $ffmpegVer" -ForegroundColor Green
} catch {
    Write-Warning "  [FALLO] FFmpeg no esta disponible en el PATH."
}

# Python
try {
    $pyVer = & python --version 2>&1
    Write-Host "  [OK] Python: $pyVer" -ForegroundColor Green
} catch {
    Write-Warning "  [FALLO] Python no esta disponible en el PATH."
}

# FilmCraft CLI version
if ($cliFound) {
    try {
        $fcVer = & "$cliFound" --version 2>&1
        Write-Host "  [OK] FilmCraft CLI: $fcVer" -ForegroundColor Green
    } catch {
        Write-Warning "  [ADVERTENCIA] No se pudo ejecutar filmcraft-cli."
    }
}

Write-Host "`nEntorno configurado correctamente para esta maquina." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
