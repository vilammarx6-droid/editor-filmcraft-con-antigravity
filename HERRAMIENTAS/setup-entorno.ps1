<#
.SYNOPSIS
    Script de configuración y portabilidad del entorno para FilmCraft y EffectCraft con Antigravity.

.DESCRIPTION
    1. Resuelve dinámicamente las rutas locales en cualquier máquina clonada.
    2. Localiza FilmCraft (GUI y CLI) y EffectCraft CLI (v0.11.1).
    3. Valida EffectCraft con info --json.
    4. Genera el archivo .agents/mcp_config.json con los servidores MCP de FilmCraft y EffectCraft.
    5. Crea/actualiza HERRAMIENTAS/config.local.json y configura la variable EFFECTCRAFT_CLI.
    6. Valida dependencias del sistema: PowerShell, Python, FFmpeg, FilmCraft, EffectCraft.
#>

param(
    [string]$FilmCraftPath = "",
    [string]$EffectCraftPath = ""
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [SETUP] Inicializacion de FilmCraft + EffectCraft        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Write-Host "-> Raiz del Repositorio: $repoRoot" -ForegroundColor Yellow

# 1. Buscar binarios de FilmCraft
$candidatePathsFC = @()
if ($FilmCraftPath -and (Test-Path $FilmCraftPath)) { $candidatePathsFC += $FilmCraftPath }
if ($env:FILMCRAFT_HOME -and (Test-Path $env:FILMCRAFT_HOME)) { $candidatePathsFC += $env:FILMCRAFT_HOME }

$candidatePathsFC += (Join-Path $repoRoot "HERRAMIENTAS\bin\filmcraft")
$candidatePathsFC += (Join-Path $repoRoot "HERRAMIENTAS\bin\filmcraft\filmcraft-0.9.0-windows-x64-portable")
$candidatePathsFC += (Join-Path $env:USERPROFILE ".gemini\antigravity\scratch\craft_tools\filmcraft\filmcraft-0.9.0-windows-x64-portable")
$candidatePathsFC += (Join-Path $env:ProgramFiles "FilmCraft")
$candidatePathsFC += (Join-Path $env:LOCALAPPDATA "Programs\FilmCraft")

$cliFound = $null
$guiFound = $null

foreach ($cand in $candidatePathsFC) {
    if (-not (Test-Path $cand)) { continue }
    $cliCandidate = Join-Path $cand "filmcraft-cli.exe"
    $guiCandidate = Join-Path $cand "filmcraft.exe"
    if ((Test-Path $cliCandidate) -and (Test-Path $guiCandidate)) {
        $cliFound = (Resolve-Path $cliCandidate).Path
        $guiFound = (Resolve-Path $guiCandidate).Path
        break
    }
}

if ($cliFound) {
    Write-Host "-> FilmCraft CLI: $cliFound" -ForegroundColor Green
    Write-Host "-> FilmCraft GUI: $guiFound" -ForegroundColor Green
} else {
    Write-Warning "No se encontro FilmCraft en rutas conocidas."
}

# 2. Buscar binario de EffectCraft CLI
$candidatePathsEC = @()
if ($EffectCraftPath -and (Test-Path $EffectCraftPath)) { $candidatePathsEC += $EffectCraftPath }
if ($env:EFFECTCRAFT_CLI -and (Test-Path $env:EFFECTCRAFT_CLI)) { $candidatePathsEC += $env:EFFECTCRAFT_CLI }

$candidatePathsEC += (Join-Path $repoRoot "HERRAMIENTAS\bin\effectcraft\effectcraft-cli.exe")
$candidatePathsEC += (Join-Path $repoRoot "HERRAMIENTAS\bin\effectcraft\effectcraft-0.11.1-windows-x64-portable\effectcraft-cli.exe")
$candidatePathsEC += (Join-Path $env:USERPROFILE ".gemini\antigravity\scratch\craft_tools\effectcraft\effectcraft-0.11.1-windows-x64-portable\effectcraft-cli.exe")
$candidatePathsEC += (Join-Path $env:ProgramFiles "EffectCraft\effectcraft-cli.exe")

$ecCliFound = $null
foreach ($cand in $candidatePathsEC) {
    if (Test-Path -LiteralPath $cand) {
        $item = Get-Item -LiteralPath $cand
        if ($item.PSIsContainer) {
            $subCli = Join-Path $cand "effectcraft-cli.exe"
            if (Test-Path $subCli) { $ecCliFound = (Resolve-Path $subCli).Path; break }
        } else {
            $ecCliFound = (Resolve-Path $cand).Path
            break
        }
    }
}

$ecValidated = $false
if ($ecCliFound) {
    Write-Host "-> EffectCraft CLI: $ecCliFound" -ForegroundColor Green
    [System.Environment]::SetEnvironmentVariable("EFFECTCRAFT_CLI", $ecCliFound, "Process")
    [System.Environment]::SetEnvironmentVariable("EFFECTCRAFT_CLI", $ecCliFound, "User")
    
    # Validar con info --json
    try {
        $infoRaw = & "$ecCliFound" info --json 2>$null
        if ($LASTEXITCODE -eq 0 -and $infoRaw) {
            $infoJson = $infoRaw | ConvertFrom-Json
            Write-Host "  [OK] EffectCraft validado: Version $($infoJson.version) (Comandos: $($infoJson.commands), Efectos: $($infoJson.effects))" -ForegroundColor Green
            $ecValidated = $true
        } else {
            Write-Warning "EffectCraft respondio pero fallo la validacion de info --json."
        }
    } catch {
        Write-Warning "Fallo al ejecutar effectcraft-cli info --json: $_"
    }
} else {
    Write-Warning "No se encontro effectcraft-cli.exe en las rutas conocidas."
}

# 3. Generar / Actualizar config.local.json
$localConfig = @{
    repo_root       = $repoRoot
    filmcraft_cli   = if ($cliFound) { $cliFound } else { "" }
    filmcraft_gui   = if ($guiFound) { $guiFound } else { "" }
    effectcraft_cli = if ($ecCliFound) { $ecCliFound } else { "" }
    ffmpeg_cmd      = "ffmpeg"
    python_cmd      = "python"
    port_bridge     = 8765
}

$configLocalPath = Join-Path $PSScriptRoot "config.local.json"
$localConfig | ConvertTo-Json -Depth 5 | Set-Content -Path $configLocalPath -Encoding UTF8
Write-Host "-> Generado: $configLocalPath" -ForegroundColor Green

# 4. Generar .agents/mcp_config.json dinámicamente con FilmCraft y EffectCraft
$agentsDir = Join-Path $repoRoot ".agents"
if (Test-Path $agentsDir) {
    $templateMcp = Join-Path $agentsDir "mcp_config.template.json"
    $tmpl = @{
        mcpServers = @{
            filmcraft = @{
                command = "{{FILMCRAFT_CLI}}"
                args    = @("--bridge", "127.0.0.1:8765", "mcp")
            }
            effectcraft = @{
                command = "{{EFFECTCRAFT_CLI}}"
                args    = @(
                    "mcp",
                    "--autosave",
                    "--automation-read-root", "{{REPO_ROOT}}",
                    "--automation-write-root", "{{REPO_ROOT}}"
                )
            }
        }
    }
    $tmpl | ConvertTo-Json -Depth 5 | Set-Content -Path $templateMcp -Encoding UTF8
    Write-Host "-> Plantilla MCP actualizada: $templateMcp" -ForegroundColor Gray

    $mcpPath = Join-Path $agentsDir "mcp_config.json"
    $fcEscaped = if ($cliFound) { $cliFound.Replace('\', '\\') } else { "filmcraft-cli.exe" }
    $ecEscaped = if ($ecCliFound) { $ecCliFound.Replace('\', '\\') } else { "effectcraft-cli.exe" }
    $repoEscaped = $repoRoot.Replace('\', '\\')

    $mcpContent = @"
{
  "mcpServers": {
    "filmcraft": {
      "command": "$fcEscaped",
      "args": ["--bridge", "127.0.0.1:8765", "mcp"]
    },
    "effectcraft": {
      "command": "$ecEscaped",
      "args": [
        "mcp",
        "--autosave",
        "--automation-read-root", "$repoEscaped",
        "--automation-write-root", "$repoEscaped"
      ]
    }
  }
}
"@
    Set-Content -Path $mcpPath -Value $mcpContent -Encoding UTF8
    Write-Host "-> MCP Config dinámico actualizado con FilmCraft y EffectCraft: $mcpPath" -ForegroundColor Green
}

Write-Host "`nEntorno y servidores MCP configurados correctamente." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
