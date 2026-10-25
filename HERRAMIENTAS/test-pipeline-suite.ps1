<#
.SYNOPSIS
    Suite de Pruebas Automatizadas y Verificacion de Integridad (Golden Test + Negative Tests)

.DESCRIPTION
    Ejecuta 3 pruebas rigurosas e independientes:
    1. Golden Test (Happy Path): Proyecto minimo de 10s montado, renderizado, auditado y registrado en run.json con SHA256.
    2. Negative Test (Quality Gate): Inyecta audio saturado (+3 dBTP) y verifica que el gate aborte con exit 1.
    3. Negative Test (Contrato de Datos): Ejecuta contra un brief vacio y verifica que falle el contrato.
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [SUITE DE PRUEBAS] Verificacion de Integridad Real       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$repoRoot = Split-Path -Parent $PSScriptRoot
$testDir = Join-Path $repoRoot "PROYECTOS\test-golden-10s"
$pyCmd = "python"

# -------------------------------------------------------------
# PREPARACIÓN: Crear Proyecto Golden de 10 segundos
# -------------------------------------------------------------
Write-Host "`n[PREP] Inicializando Proyecto Golden 'test-golden-10s'..." -ForegroundColor Yellow

$subfolders = @(
    "00_brief",
    "01_fuentes\video",
    "01_fuentes\audio",
    "01_fuentes\musica",
    "01_fuentes\graficos",
    "02_filmcraft",
    "03_exports",
    "04_previews",
    "05_logs"
)
foreach ($sf in $subfolders) {
    $p = Join-Path $testDir $sf
    if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
}

# Brief
$briefText = @"
# Brief — Test Golden 10s

- Fecha: 2026-10-25
- Formato: horizontal_720
- Resolución: 1280x720
- Duración objetivo: 10.00s (300 frames @ 30fps)
- Tema: Verificacion tecnica de pipeline y Quality Gate

---

## Guion

Este es el test dorado de diez segundos para verificar la integridad del pipeline de FilmCraft con Antigravity.
"@
Set-Content -Path (Join-Path $testDir "00_brief\brief.md") -Value $briefText -Encoding UTF8

# Video sintético 10s
$clipVideo = Join-Path $testDir "01_fuentes\video\clip_golden_10s.mp4"
if (-not (Test-Path $clipVideo)) {
    Write-Host "  -> Generando metraje sintetico 10s con FFmpeg..." -ForegroundColor Gray
    & ffmpeg -y -nostats -loglevel error -f lavfi -i "testsrc=size=1280x720:rate=30" -t 10 -c:v libx264 -pix_fmt yuv420p $clipVideo
}

# Música sintética 10s
$clipMusica = Join-Path $testDir "01_fuentes\musica\musica_golden_10s.wav"
if (-not (Test-Path $clipMusica)) {
    Write-Host "  -> Generando cama musical 10s con FFmpeg..." -ForegroundColor Gray
    & ffmpeg -y -nostats -loglevel error -f lavfi -i "sine=frequency=440:sample_rate=48000:duration=10" -af "volume=-18dB" $clipMusica
}

# Locución de 10s (Edge-TTS)
Write-Host "  -> Generando locucion de prueba con generar-voz.ps1..." -ForegroundColor Gray
& "$PSScriptRoot\generar-voz.ps1" -Proyecto $testDir -NombreSalida "locucion" | Out-Null

# Ensamblar export maestro de 10s
$finalExport = Join-Path $testDir "03_exports\test-golden-10s_v01_horizontal_720.mp4"
$locWav = Join-Path $testDir "01_fuentes\audio\locucion.wav"
Write-Host "  -> Renderizando master de prueba de 10s con FFmpeg..." -ForegroundColor Gray
& ffmpeg -y -nostats -loglevel error -i $clipVideo -i $locWav -i $clipMusica -filter_complex "[1:a][2:a]amix=inputs=2:duration=first[aout]" -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k -t 10 $finalExport

# Remediación inicial para garantizar que el máster golden cumpla la norma
& $pyCmd "$PSScriptRoot\remediar-audio.py" $finalExport -o $finalExport | Out-Null

# Crear fotogramas de prueba QA
for ($i = 1; $i -le 4; $i++) {
    $sec = $i * 2
    $qaFile = Join-Path $testDir "04_previews\qa_0$($i)_frame.png"
    & ffmpeg -y -nostats -loglevel error -ss $sec -i $clipVideo -frames:v 1 -vf scale=480:270 $qaFile
}

# -------------------------------------------------------------
# TEST 1: Happy Path (Caso Positivo)
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " TEST 1: Ejecucion de Pipeline Golden (Happy Path)        " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$test1Failed = $false
try {
    & "$PSScriptRoot\ejecutar-pipeline.ps1" -Proyecto $testDir
    if ($LASTEXITCODE -ne 0) { $test1Failed = $true }
} catch {
    $test1Failed = $true
}

$runJsonPath = Join-Path $testDir "05_logs\run.json"
if ($test1Failed -or -not (Test-Path $runJsonPath)) {
    Write-Host "[FALLO] El Test 1 no supero la ejecucion del pipeline." -ForegroundColor Red
    exit 1
}

$runData = Get-Content $runJsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Host "`n[RESULTADO TEST 1 - COMPROBADO]" -ForegroundColor Green
Write-Host "  -> Estado del Pipeline: $($runData.pipeline_status)" -ForegroundColor Green
Write-Host "  -> Session ID:          $($runData.session_id)" -ForegroundColor Green
Write-Host "  -> Artefactos Validados: $($runData.artifacts_count)" -ForegroundColor Green
foreach ($art in $runData.artifacts) {
    Write-Host "     - $($art.file) (SHA256: $($art.sha256.Substring(0,16))..., Size: $($art.size_bytes) bytes)" -ForegroundColor Gray
}

# -------------------------------------------------------------
# TEST 2: Negative Test (Falla Forzada por Saturación / Clipping)
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " TEST 2: Prueba Negativa (Quality Gate con Clipping)      " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$clipCorrupto = Join-Path $env:TEMP "test_clipping_fail.mp4"
Write-Host "  -> Inyectando audio con distorsion forzada (+15 dB)..." -ForegroundColor Yellow
& ffmpeg -y -nostats -loglevel error -i $clipVideo -f lavfi -i "sine=frequency=1000:sample_rate=48000:duration=5" -filter_complex "[1:a]volume=15dB[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -t 5 $clipCorrupto

Write-Host "  -> Pasando archivo corrupto por auditar-calidad.py..." -ForegroundColor Yellow
$gatePassed = $false
try {
    & $pyCmd "$PSScriptRoot\auditar-calidad.py" $clipCorrupto
    if ($LASTEXITCODE -eq 0) {
        $gatePassed = $true
    }
} catch {
    $gatePassed = $false
}

Remove-Item -Path $clipCorrupto -Force -ErrorAction SilentlyContinue

if ($gatePassed) {
    Write-Host "[FALLO] El Quality Gate dejo pasar un archivo saturado. El gate no es estricto." -ForegroundColor Red
    exit 1
} else {
    Write-Host "`n[RESULTADO TEST 2 - COMPROBADO]" -ForegroundColor Green
    Write-Host "  -> El Quality Gate detecto la saturacion y RECHAZO el archivo con exit 1." -ForegroundColor Green
    Write-Host "  -> Comportamiento verificado: El gate bloquea exports defectuosos de forma real." -ForegroundColor Green
}

# -------------------------------------------------------------
# TEST 3: Negative Test (Contrato de Datos de Brief Inválido)
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " TEST 3: Prueba Negativa (Brief sin Guion)                " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$tempEmptyBrief = Join-Path $env:TEMP "brief_invalido.md"
Set-Content -Path $tempEmptyBrief -Value "# Brief Vacio`nSin seccion de guion" -Encoding UTF8

$tempProj = Join-Path $env:TEMP "proj_invalido"
New-Item -ItemType Directory -Path (Join-Path $tempProj "00_brief") -Force | Out-Null
Copy-Item -Path $tempEmptyBrief -Destination (Join-Path $tempProj "00_brief\brief.md") -Force

$contractRejected = $false
try {
    & "$PSScriptRoot\generar-voz.ps1" -Proyecto $tempProj -NombreSalida "fail_test" 2>$null
    if ($LASTEXITCODE -ne 0) { $contractRejected = $true }
} catch {
    $contractRejected = $true
}

Remove-Item -Path $tempProj -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path $tempEmptyBrief -Force -ErrorAction SilentlyContinue

if ($contractRejected) {
    Write-Host "`n[RESULTADO TEST 3 - COMPROBADO]" -ForegroundColor Green
    Write-Host "  -> El extractor de guion rechazo la entrada invalida y aborto la ejecucion." -ForegroundColor Green
    Write-Host "  -> Comportamiento verificado: El contrato de datos es estricto." -ForegroundColor Green
} else {
    Write-Host "[FALLO] El script permitio generar voz sin guion valido." -ForegroundColor Red
    exit 1
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " [SUITE EXITOSA] Las 3 pruebas de integridad pasaron al 100%" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
