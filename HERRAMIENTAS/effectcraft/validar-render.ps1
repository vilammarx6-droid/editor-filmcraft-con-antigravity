<#
.SYNOPSIS
    Suite de Validacion y Pruebas Negativas para EffectCraft (validar-render.ps1)

.DESCRIPTION
    Ejecuta las pruebas de contrato y validacion estricta:
    1. Happy Path 1: Renderizado de overlay animado en ProRes 4444 con canal alfa real.
    2. Happy Path 2: Renderizado de fotograma PNG RGBA transparente.
    3. Negative Test 1: Fallo forzado por tipo incorrecto (string en lugar de color).
    4. Negative Test 2: Fallo forzado por comp que no coincide.
    5. Negative Test 3: Fallo forzado por transparencia sin alfa (channels rgba con h264).
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [EFFECTCRAFT] Suite de Validacion y Pruebas Negativas    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$scriptDir = $PSScriptRoot
$templatePath = Join-Path $scriptDir "templates\lower_third_clean.ectemplate"
$ecRenderPy = Join-Path $scriptDir "ec_render.py"
$tempDir = Join-Path $env:TEMP "ec_tests_$([Guid]::NewGuid().ToString().Substring(0,8))"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

if (-not (Test-Path $templatePath)) {
    Write-Host "-> Generando template limpio antes de iniciar pruebas..." -ForegroundColor Yellow
    python (Join-Path $scriptDir "crear_template_lower_third.py")
}

# -------------------------------------------------------------
# PRUEBA 1: Happy Path - ProRes 4444 RGBA con Alfa
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " PRUEBA 1: Happy Path (Video Overlay ProRes 4444 RGBA)   " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$diseno1 = @{
    template = $templatePath
    comp     = "Lower Third"
    values   = @{
        "Name"      = "Dr. Alejandro"
        "Title"     = "Especialista Clinico - MediFlow"
        "Bar Color" = @(0.0, 0.9, 0.6, 1.0)
    }
    fps      = 30
    start    = 0.0
    end      = 1.5
    format   = "prores"
    channels = "rgba"
    output   = (Join-Path $tempDir "overlay_alejandro.mov")
}

$diseno1Path = Join-Path $tempDir "diseno_prores_ok.json"
$diseno1 | ConvertTo-Json -Depth 5 | Set-Content -Path $diseno1Path -Encoding UTF8

python $ecRenderPy $diseno1Path
$p1Exit = $LASTEXITCODE

$manifest1Path = Join-Path $tempDir "render-manifest.json"
if ($p1Exit -eq 0 -and (Test-Path $manifest1Path)) {
    $m1 = Get-Content $manifest1Path -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($m1.status -eq "ok" -and $m1.has_alpha -eq $true) {
        Write-Host "`n[PRUEBA 1 PASADA] ProRes 4444 renderizado con canal alfa real y manifest verificado." -ForegroundColor Green
        Write-Host "  -> SHA256:  $($m1.sha256)" -ForegroundColor Gray
        Write-Host "  -> PixFmt:  $($m1.pix_fmt) (Alfa confirmado)" -ForegroundColor Gray
        Write-Host "  -> Frames:  $($m1.frames_count) frames" -ForegroundColor Gray
    } else {
        Write-Host "[FALLO] El manifest no confirmo el canal alfa." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[FALLO] Error ejecutando Prueba 1." -ForegroundColor Red
    exit 1
}

# -------------------------------------------------------------
# PRUEBA 2: Happy Path - PNG RGBA Transparente
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " PRUEBA 2: Happy Path (Fotograma PNG RGBA Transparente)   " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$diseno2 = @{
    template = $templatePath
    comp     = "Lower Third"
    values   = @{
        "Name"      = "Carlos Mendoza"
        "Title"     = "Paciente Urgencia"
        "Bar Color" = @(0.9, 0.2, 0.2, 1.0)
    }
    fps      = 30
    start    = 1.0
    end      = 1.0
    format   = "png"
    channels = "rgba"
    output   = (Join-Path $tempDir "carlos_tag.png")
}

$diseno2Path = Join-Path $tempDir "diseno_png_ok.json"
$diseno2 | ConvertTo-Json -Depth 5 | Set-Content -Path $diseno2Path -Encoding UTF8

python $ecRenderPy $diseno2Path
$p2Exit = $LASTEXITCODE

$manifest2Path = Join-Path $tempDir "render-manifest.json"
if ($p2Exit -eq 0 -and (Test-Path $manifest2Path)) {
    $m2 = Get-Content $manifest2Path -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($m2.status -eq "ok" -and $m2.has_alpha -eq $true) {
        Write-Host "`n[PRUEBA 2 PASADA] PNG RGBA renderizado con transparencia real confirmada por Pillow." -ForegroundColor Green
        Write-Host "  -> Modo: $($m2.pix_fmt) (RGBA)" -ForegroundColor Gray
        Write-Host "  -> Resolucion: $($m2.dimensions[0])x$($m2.dimensions[1])" -ForegroundColor Gray
    } else {
        Write-Host "[FALLO] El PNG no contiene canal alfa." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[FALLO] Error ejecutando Prueba 2." -ForegroundColor Red
    exit 1
}

# -------------------------------------------------------------
# PRUEBA 3: Prueba Negativa - Tipo Incorrecto
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " PRUEBA 3: Negativa (Tipo Incorrecto: String por Color)   " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$diseno3 = @{
    template = $templatePath
    comp     = "Lower Third"
    values   = @{
        "Name"      = "Test Error"
        "Title"     = "Cargo"
        "Bar Color" = "azul_invalido" # Deberia ser un array numerico [r,g,b,a]
    }
    format   = "png"
    channels = "rgba"
    output   = (Join-Path $tempDir "error_tipo.png")
}

$diseno3Path = Join-Path $tempDir "diseno_fail_tipo.json"
$diseno3 | ConvertTo-Json -Depth 5 | Set-Content -Path $diseno3Path -Encoding UTF8

$outputErr3 = python $ecRenderPy $diseno3Path 2>&1
$p3Exit = $LASTEXITCODE

if ($p3Exit -ne 0 -and ($outputErr3 -match "Tipo incorrecto")) {
    Write-Host "[PRUEBA 3 PASADA] El validador detecto el tipo incorrecto y rechazo el render con exit 1." -ForegroundColor Green
} else {
    Write-Host "[FALLO] Se esperaba que el validador abortara por tipo incorrecto." -ForegroundColor Red
    exit 1
}

# -------------------------------------------------------------
# PRUEBA 4: Prueba Negativa - Comp que no coincide
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " PRUEBA 4: Negativa (Comp que no coincide)               " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$diseno4 = @{
    template = $templatePath
    comp     = "ComposicionFalsaInexistente"
    values   = @{ "Name" = "Test" }
    format   = "png"
    channels = "rgba"
    output   = (Join-Path $tempDir "error_comp.png")
}

$diseno4Path = Join-Path $tempDir "diseno_fail_comp.json"
$diseno4 | ConvertTo-Json -Depth 5 | Set-Content -Path $diseno4Path -Encoding UTF8

$outputErr4 = python $ecRenderPy $diseno4Path 2>&1
$p4Exit = $LASTEXITCODE

if ($p4Exit -ne 0 -and ($outputErr4 -match "Comp que no coincide")) {
    Write-Host "[PRUEBA 4 PASADA] El validador detecto la discordancia de composicion y aborto con exit 1." -ForegroundColor Green
} else {
    Write-Host "[FALLO] Se esperaba que el validador abortara por comp no coincidente." -ForegroundColor Red
    exit 1
}

# -------------------------------------------------------------
# PRUEBA 5: Prueba Negativa - Transparencia sin Alfa
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " PRUEBA 5: Negativa (Transparencia sin Alfa: RGBA en H264)" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$diseno5 = @{
    template = $templatePath
    comp     = "Lower Third"
    values   = @{ "Name" = "Test" }
    format   = "h264"
    channels = "rgba" # Incompatible: H.264 no soporta canal alfa
    output   = (Join-Path $tempDir "error_alfa.mp4")
}

$diseno5Path = Join-Path $tempDir "diseno_fail_alfa.json"
$diseno5 | ConvertTo-Json -Depth 5 | Set-Content -Path $diseno5Path -Encoding UTF8

$outputErr5 = python $ecRenderPy $diseno5Path 2>&1
$p5Exit = $LASTEXITCODE

if ($p5Exit -ne 0 -and ($outputErr5 -match "Transparencia sin alfa")) {
    Write-Host "[PRUEBA 5 PASADA] El validador impidio solicitar transparencia sobre un codec sin alfa." -ForegroundColor Green
} else {
    Write-Host "[FALLO] Se esperaba que el validador abortara por incompatibilidad de canal alfa." -ForegroundColor Red
    exit 1
}

# Limpieza
Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " [SUITE EXITOSA] Las 5 pruebas de EffectCraft pasaron al 100%" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
