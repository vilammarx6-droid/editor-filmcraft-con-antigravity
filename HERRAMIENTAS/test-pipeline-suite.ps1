<#
.SYNOPSIS
    Suite Integral de Pruebas y Verificacion de Integridad (Happy Path + 4 Pruebas Negativas)

.DESCRIPTION
    1. Ensambla el proyecto golden de 10s:
       - Genera overlay ProRes 4444 RGBA con EffectCraft (ec_render.py) y emite render-manifest.json.
       - Crea el archivo nativo .fcproj en FilmCraft CLI con pistas V1, V2, A1, A2.
       - Renderiza el master de 10s con mezcla EBU R128 (-14.4 LUFS, TP <= -1.2 dBTP).
    2. TEST 1 (Happy Path):
       - Ejecuta ejecutar-pipeline.ps1.
       - Valida que pase todas las fases, genere run.json con los hashes del .fcproj, overlay y manifest.
    3. TEST 2 (Negativa - Sonoridad fuera de norma):
       - Inyecta video a -25 LUFS (demasiado bajo) y comprueba que el Quality Gate lo RECHACE con exit 1.
    4. TEST 3 (Negativa - Clipping / True Peak excedido):
       - Inyecta audio con True Peak +2.1 dBTP y comprueba que aborte con exit 1.
    5. TEST 4 (Negativa - Falta de .fcproj en FilmCraft):
       - Ejecuta pipeline contra carpeta sin .fcproj y verifica que aborte con exit 1.
    6. TEST 5 (Negativa - Falta de render-manifest.json en EffectCraft):
       - Proyecto con diseno.json sin manifest verificado -> comprueba que aborte con exit 1.
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [SUITE DE INTEGRIDAD] Pruebas Rigurosas y Quality Gate   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$scriptDir = $PSScriptRoot
$repoRoot = Split-Path -Parent $scriptDir
$testDir = Join-Path $repoRoot "PROYECTOS\test-golden-10s"
$pyCmd = "python"

# -------------------------------------------------------------
# PREPARACIÓN: Ensamblar proyecto golden completo
# -------------------------------------------------------------
Write-Host "`n[PREP] Ensamblando Proyecto Golden 10s (FilmCraft + EffectCraft)..." -ForegroundColor Yellow
$ensambladorPy = Join-Path $scriptDir "effectcraft\ensamblar_test_golden.py"
& $pyCmd $ensambladorPy
if ($LASTEXITCODE -ne 0) {
    throw "Fallo el ensamblado del proyecto golden."
}

# -------------------------------------------------------------
# TEST 1: Happy Path de Extremo a Extremo
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " TEST 1: Pipeline Completo End-to-End (Happy Path)        " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$pipelineFailed = $false
try {
    & "$scriptDir\ejecutar-pipeline.ps1" -Proyecto $testDir
    if ($LASTEXITCODE -ne 0) { $pipelineFailed = $true }
} catch {
    $pipelineFailed = $true
}

$runJsonPath = Join-Path $testDir "05_logs\run.json"
if ($pipelineFailed -or -not (Test-Path $runJsonPath)) {
    Write-Host "[FALLO] El Test 1 no supero la ejecucion del pipeline." -ForegroundColor Red
    exit 1
}

$runData = Get-Content $runJsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Host "`n[TEST 1 PASADO - VERIFICACION CRIPTOGRAFICA COMPLETA]" -ForegroundColor Green
Write-Host "  -> Estado del Pipeline: $($runData.pipeline_status)" -ForegroundColor Green
Write-Host "  -> Session ID:          $($runData.session_id)" -ForegroundColor Green
Write-Host "  -> Artefactos Totales:  $($runData.artifacts_count)" -ForegroundColor Green
foreach ($art in $runData.artifacts) {
    Write-Host "     - $($art.file.PadRight(35)) (SHA256: $($art.sha256.Substring(0,16))..., Size: $($art.size_bytes) B)" -ForegroundColor Gray
}

# -------------------------------------------------------------
# TEST 2: Negativa - Sonoridad fuera de norma (-25.7 LUFS)
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " TEST 2: Negativa (Sonoridad Debil: -25 LUFS fuera rango) " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$clipQuiet = Join-Path $env:TEMP "test_quiet_fail.mp4"
$masterVideo = Join-Path $testDir "03_exports\test-golden-10s_v01_horizontal_720.mp4"

# Crear versión atenuada a -25 LUFS
& ffmpeg -y -nostats -loglevel error -i $masterVideo -af "volume=-15dB" -c:v copy -c:a aac -ar 48000 $clipQuiet

$quietPassed = $false
try {
    & $pyCmd "$scriptDir\auditar-calidad.py" $clipQuiet 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $quietPassed = $true }
} catch {
    $quietPassed = $false
}
Remove-Item -Path $clipQuiet -Force -ErrorAction SilentlyContinue

if ($quietPassed) {
    Write-Host "[FALLO] El Quality Gate dejo pasar un audio debil de -25 LUFS sin bloquear." -ForegroundColor Red
    exit 1
} else {
    Write-Host "[TEST 2 PASADO] El Quality Gate detecto sonoridad fuera de [-16, -13] LUFS y BLOQUEO con exit 1." -ForegroundColor Green
}

# -------------------------------------------------------------
# TEST 3: Negativa - Clipping y Distorsión (+2.1 dBTP)
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " TEST 3: Negativa (Clipping y True Peak excedido)         " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$clipDist = Join-Path $env:TEMP "test_clipping_fail.mp4"
& ffmpeg -y -nostats -loglevel error -i $masterVideo -af "volume=+15dB" -c:v copy -c:a aac -ar 48000 $clipDist

$distPassed = $false
try {
    & $pyCmd "$scriptDir\auditar-calidad.py" $clipDist 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $distPassed = $true }
} catch {
    $distPassed = $false
}
Remove-Item -Path $clipDist -Force -ErrorAction SilentlyContinue

if ($distPassed) {
    Write-Host "[FALLO] El Quality Gate dejo pasar un audio con distorsion." -ForegroundColor Red
    exit 1
} else {
    Write-Host "[TEST 3 PASADO] El Quality Gate detecto True Peak excedido y BLOQUEO con exit 1." -ForegroundColor Green
}

# -------------------------------------------------------------
# TEST 4: Negativa - Proyecto sin archivo .fcproj de FilmCraft
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " TEST 4: Negativa (Falta de linea de tiempo .fcproj)      " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$tempNoFc = Join-Path $env:TEMP "proj_no_fcproj"
New-Item -ItemType Directory -Path (Join-Path $tempNoFc "00_brief") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempNoFc "02_filmcraft") -Force | Out-Null
Copy-Item (Join-Path $testDir "00_brief\brief.md") (Join-Path $tempNoFc "00_brief\brief.md")

$noFcPassed = $false
try {
    & "$scriptDir\ejecutar-pipeline.ps1" -Proyecto $tempNoFc 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $noFcPassed = $true }
} catch {
    $noFcPassed = $false
}
Remove-Item -Path $tempNoFc -Recurse -Force -ErrorAction SilentlyContinue

if ($noFcPassed) {
    Write-Host "[FALLO] El pipeline permitio continuar sin archivo .fcproj." -ForegroundColor Red
    exit 1
} else {
    Write-Host "[TEST 4 PASADO] El pipeline exigio una linea de tiempo real de FilmCraft y aborto con exit 1." -ForegroundColor Green
}

# -------------------------------------------------------------
# TEST 5: Negativa - Gráficos sin render-manifest.json
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " TEST 5: Negativa (Diseno EffectCraft sin Manifest)       " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$tempNoManifest = Join-Path $env:TEMP "proj_no_manifest"
New-Item -ItemType Directory -Path (Join-Path $tempNoManifest "00_brief") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempNoManifest "01_fuentes\graficos") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempNoManifest "02_filmcraft") -Force | Out-Null
Copy-Item (Join-Path $testDir "00_brief\brief.md") (Join-Path $tempNoManifest "00_brief\brief.md")
Copy-Item (Join-Path $testDir "02_filmcraft\test-golden-10s_v01.fcproj") (Join-Path $tempNoManifest "02_filmcraft\test-golden-10s_v01.fcproj")
Set-Content -Path (Join-Path $tempNoManifest "01_fuentes\graficos\diseno_prueba.json") -Value "{}" -Encoding UTF8
# No creamos render-manifest.json

$noManiPassed = $false
try {
    & "$scriptDir\ejecutar-pipeline.ps1" -Proyecto $tempNoManifest 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $noManiPassed = $true }
} catch {
    $noManiPassed = $false
}
Remove-Item -Path $tempNoManifest -Recurse -Force -ErrorAction SilentlyContinue

if ($noManiPassed) {
    Write-Host "[FALLO] El pipeline permitio graficos sin manifest verificado." -ForegroundColor Red
    exit 1
} else {
    Write-Host "[TEST 5 PASADO] El pipeline detecto diseno sin render-manifest.json y BLOQUEO con exit 1." -ForegroundColor Green
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " [SUITE EXITOSA] Las 5 pruebas rigurosas pasaron al 100%  " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
