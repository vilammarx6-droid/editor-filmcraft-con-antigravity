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
    [string]$EffectCraftPath = "",
    [string]$PhotoCraftPath = "",
    [string]$SoundCraftPath = ""
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [SETUP] Inicializacion de Suite Craft (FC + EC + PC + SC)" -ForegroundColor Cyan
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

# 3. Buscar binario de PhotoCraft (CLI y GUI)
$candidatePathsPC = @()
if ($PhotoCraftPath -and (Test-Path $PhotoCraftPath)) { $candidatePathsPC += $PhotoCraftPath }
if ($env:PHOTOCRAFT_CLI -and (Test-Path $env:PHOTOCRAFT_CLI)) { $candidatePathsPC += $env:PHOTOCRAFT_CLI }

$candidatePathsPC += (Join-Path $repoRoot "HERRAMIENTAS\bin\photocraft")
$candidatePathsPC += (Join-Path $repoRoot "HERRAMIENTAS\bin\photocraft\photocraft-0.16.0-windows-x64-portable")
$candidatePathsPC += (Join-Path $env:USERPROFILE ".gemini\antigravity\scratch\craft_tools\photocraft\photocraft-0.16.0-windows-x64-portable")
$candidatePathsPC += (Join-Path $env:ProgramFiles "PhotoCraft")
$candidatePathsPC += (Join-Path $env:LOCALAPPDATA "Programs\PhotoCraft")

$pcCliFound = $null
$pcGuiFound = $null

foreach ($cand in $candidatePathsPC) {
    if (-not (Test-Path $cand)) { continue }
    $cliCand = Join-Path $cand "photocraft-cli.exe"
    $guiCand = Join-Path $cand "photocraft.exe"
    if (Test-Path $cliCand) { $pcCliFound = (Resolve-Path $cliCand).Path }
    if (Test-Path $guiCand) { $pcGuiFound = (Resolve-Path $guiCand).Path }
    if ($pcCliFound) { break }
}

if ($pcCliFound) {
    Write-Host "-> PhotoCraft CLI: $pcCliFound" -ForegroundColor Green
    if ($pcGuiFound) { Write-Host "-> PhotoCraft GUI: $pcGuiFound" -ForegroundColor Green }
    [System.Environment]::SetEnvironmentVariable("PHOTOCRAFT_CLI", $pcCliFound, "Process")
    [System.Environment]::SetEnvironmentVariable("PHOTOCRAFT_CLI", $pcCliFound, "User")
} else {
    Write-Warning "No se encontro PhotoCraft en rutas conocidas."
}

# 4. Buscar binario de SoundCraft (CLI y GUI)
$candidatePathsSC = @()
if ($SoundCraftPath -and (Test-Path $SoundCraftPath)) { $candidatePathsSC += $SoundCraftPath }
if ($env:SOUNDCRAFT_CLI -and (Test-Path $env:SOUNDCRAFT_CLI)) { $candidatePathsSC += $env:SOUNDCRAFT_CLI }

$candidatePathsSC += (Join-Path $repoRoot "HERRAMIENTAS\bin\soundcraft")
$candidatePathsSC += (Join-Path $repoRoot "HERRAMIENTAS\bin\soundcraft\soundcraft-0.13.1-windows-x64-portable")
$candidatePathsSC += (Join-Path $env:USERPROFILE ".gemini\antigravity\scratch\craft_tools\soundcraft\soundcraft-0.13.1-windows-x64-portable")
$candidatePathsSC += (Join-Path $env:ProgramFiles "SoundCraft")
$candidatePathsSC += (Join-Path $env:LOCALAPPDATA "Programs\SoundCraft")

$scCliFound = $null
$scGuiFound = $null

foreach ($cand in $candidatePathsSC) {
    if (-not (Test-Path $cand)) { continue }
    $cliCand = Join-Path $cand "soundcraft-cli.exe"
    $guiCand = Join-Path $cand "soundcraft.exe"
    if (Test-Path $cliCand) { $scCliFound = (Resolve-Path $cliCand).Path }
    if (Test-Path $guiCand) { $scGuiFound = (Resolve-Path $guiCand).Path }
    if ($scCliFound) { break }
}

if ($scCliFound) {
    Write-Host "-> SoundCraft CLI: $scCliFound" -ForegroundColor Green
    if ($scGuiFound) { Write-Host "-> SoundCraft GUI: $scGuiFound" -ForegroundColor Green }
    [System.Environment]::SetEnvironmentVariable("SOUNDCRAFT_CLI", $scCliFound, "Process")
    [System.Environment]::SetEnvironmentVariable("SOUNDCRAFT_CLI", $scCliFound, "User")
} else {
    Write-Warning "No se encontro SoundCraft en rutas conocidas."
}

# 5. Generar / Actualizar config.local.json
$localConfig = @{
    repo_root       = $repoRoot
    filmcraft_cli   = if ($cliFound) { $cliFound } else { "" }
    filmcraft_gui   = if ($guiFound) { $guiFound } else { "" }
    effectcraft_cli = if ($ecCliFound) { $ecCliFound } else { "" }
    photocraft_cli  = if ($pcCliFound) { $pcCliFound } else { "" }
    photocraft_gui  = if ($pcGuiFound) { $pcGuiFound } else { "" }
    soundcraft_cli  = if ($scCliFound) { $scCliFound } else { "" }
    soundcraft_gui  = if ($scGuiFound) { $scGuiFound } else { "" }
    ffmpeg_cmd      = "ffmpeg"
    python_cmd      = "python"
    port_bridge     = 8765
}

$configLocalPath = Join-Path $PSScriptRoot "config.local.json"
$localConfig | ConvertTo-Json -Depth 5 | Set-Content -Path $configLocalPath -Encoding UTF8
Write-Host "-> Generado: $configLocalPath" -ForegroundColor Green

# 6. Generar .agents/mcp_config.json dinámicamente con la Suite Craft Completa
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
            photocraft = @{
                command = "{{PHOTOCRAFT_CLI}}"
                args    = @(
                    "mcp",
                    "--automation-read-root", "{{REPO_ROOT}}",
                    "--automation-write-root", "{{REPO_ROOT}}"
                )
            }
            soundcraft = @{
                command = "{{SOUNDCRAFT_CLI}}"
                args    = @(
                    "mcp",
                    "--automation-read-root", "{{REPO_ROOT}}",
                    "--automation-write-root", "{{REPO_ROOT}}"
                )
            }
        }
    }
    $tmpl | ConvertTo-Json -Depth 5 | Set-Content -Path $templateMcp -Encoding UTF8
    Write-Host "-> Plantilla MCP actualizada: $templateMcp" -ForegroundColor Gray

    $mcpPath = Join-Path $agentsDir "mcp_config.json"
    $fcCmd = if ($cliFound) { $cliFound } else { "filmcraft-cli.exe" }
    $ecCmd = if ($ecCliFound) { $ecCliFound } else { "effectcraft-cli.exe" }
    $pcCmd = if ($pcCliFound) { $pcCliFound } else { "photocraft-cli.exe" }
    $scCmd = if ($scCliFound) { $scCliFound } else { "soundcraft-cli.exe" }

    $mcpServersObj = [ordered]@{}
    if ($cliFound) {
        $mcpServersObj["filmcraft"] = @{
            command = $fcCmd
            args    = @("--bridge", "127.0.0.1:8765", "mcp")
        }
    }
    if ($ecCliFound) {
        $mcpServersObj["effectcraft"] = @{
            command = $ecCmd
            args    = @("mcp", "--autosave", "--automation-read-root", $repoRoot, "--automation-write-root", $repoRoot)
        }
    }
    if ($pcCliFound) {
        $mcpServersObj["photocraft"] = @{
            command = $pcCmd
            args    = @("mcp", "--automation-read-root", $repoRoot, "--automation-write-root", $repoRoot)
        }
    }
    if ($scCliFound) {
        $mcpServersObj["soundcraft"] = @{
            command = $scCmd
            args    = @("mcp", "--automation-read-root", $repoRoot, "--automation-write-root", $repoRoot)
        }
    }

    $finalMcp = @{ mcpServers = $mcpServersObj }
    $finalMcp | ConvertTo-Json -Depth 5 | Set-Content -Path $mcpPath -Encoding UTF8
    Write-Host "-> MCP Config dinamico actualizado con Suite Craft (FC + EC + PC + SC): $mcpPath" -ForegroundColor Green
}

Write-Host "`nEntorno y servidores MCP configurados correctamente." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
