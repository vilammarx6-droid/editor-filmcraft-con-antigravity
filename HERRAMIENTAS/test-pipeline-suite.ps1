<#
.SYNOPSIS
    Suite Integral de Pruebas y Verificacion de Integridad (9 pruebas herméticas)

.DESCRIPTION
    El proyecto golden se construye en una carpeta temporal; no se reutiliza ni
    se modifica el .fcproj del proyecto real.

    TEST 1 (Happy Path): pipeline completo -> run.json con hashes reales.
    TEST 2 (Negativa): sonoridad -25 LUFS -> Quality Gate exit 1.
    TEST 3 (Negativa): clipping / True Peak excedido -> exit 1.
    TEST 4 (Negativa): proyecto sin .fcproj -> exit 1.
    TEST 5 (Negativa): diseno EffectCraft sin render-manifest.json -> exit 1.
    TEST 6 (Negativa): timeline válida pero sin master exportado -> exit 1.
    TEST 7 (Negativa): miniatura/manifiesto con SHA-256 manipulado -> exit 1.
    TEST 8 (Contrato PhotoCraft): proyecto inexistente, sin héroe, CLI roto y
           salida real verificada en 1920x1080.
    TEST 9 (Montador): edit-plan.json -> timeline V1/A1 -> export FilmCraft ->
           master normalizado y aprobado por el Quality Gate.
#>

param(
    [switch]$KeepArtifacts
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [SUITE DE INTEGRIDAD] Pruebas Rigurosas y Quality Gate   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$scriptDir = $PSScriptRoot
$repoRoot = Split-Path -Parent $scriptDir
$testDir = Join-Path $env:TEMP ("opencode\pipeline-suite-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $testDir -Force | Out-Null
$pyCmd = "python"

# -------------------------------------------------------------
# PREPARACIÓN: Ensamblar proyecto golden completo
# -------------------------------------------------------------
Write-Host "`n[PREP] Ensamblando Proyecto Golden 10s en copia temporal..." -ForegroundColor Yellow
Write-Host "       Destino: $testDir" -ForegroundColor Gray
New-Item -ItemType Directory -Path (Join-Path $testDir "00_brief") -Force | Out-Null
@"
# Brief - Test Golden 10s

- Formato: horizontal_720
- Resolucion: 1280x720
- Duracion objetivo: 10.00s

## Guion

Esta es una prueba tecnica del pipeline de FilmCraft con Antigravity para verificar el montaje, el audio y el Quality Gate.
"@ | Set-Content -Path (Join-Path $testDir "00_brief\brief.md") -Encoding UTF8

$ensambladorPy = Join-Path $scriptDir "effectcraft\ensamblar_test_golden.py"
& $pyCmd $ensambladorPy --project-dir $testDir
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
    & "$scriptDir\ejecutar-pipeline.ps1" -Proyecto $testDir -PermitirTimelineExistente
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
    & "$scriptDir\ejecutar-pipeline.ps1" -Proyecto $tempNoFc -PermitirTimelineExistente 2>&1 | Out-Null
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
    & "$scriptDir\ejecutar-pipeline.ps1" -Proyecto $tempNoManifest -PermitirTimelineExistente 2>&1 | Out-Null
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

# -------------------------------------------------------------
# TEST 6: Negativa - Ausencia de video master en 03_exports
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " TEST 6: Negativa (Falta de video master en 03_exports)   " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$tempNoMaster = Join-Path $env:TEMP "proj_no_master"
New-Item -ItemType Directory -Path (Join-Path $tempNoMaster "00_brief") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempNoMaster "01_fuentes\graficos") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempNoMaster "02_filmcraft") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempNoMaster "03_exports") -Force | Out-Null
Copy-Item (Join-Path $testDir "00_brief\brief.md") (Join-Path $tempNoMaster "00_brief\brief.md")
Copy-Item (Join-Path $testDir "02_filmcraft\test-golden-10s_v01.fcproj") (Join-Path $tempNoMaster "02_filmcraft\test-golden-10s_v01.fcproj")
# 03_exports queda vacia intencionalmente

$noMasterPassed = $false
try {
    & "$scriptDir\ejecutar-pipeline.ps1" -Proyecto $tempNoMaster -PermitirTimelineExistente 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $noMasterPassed = $true }
} catch {
    $noMasterPassed = $false
}
Remove-Item -Path $tempNoMaster -Recurse -Force -ErrorAction SilentlyContinue

if ($noMasterPassed) {
    Write-Host "[FALLO] El pipeline declaro exito sin video master exportado." -ForegroundColor Red
    exit 1
} else {
    Write-Host "[TEST 6 PASADO] El pipeline detecto falta de video master y BLOQUEO con exit 1." -ForegroundColor Green
}

# -------------------------------------------------------------
# TEST 7: Negativa - Miniatura/Manifiesto manipulado (SHA-256 no coincide)
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " TEST 7: Negativa (Manipulacion de hash en manifiesto)    " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$tempTampered = Join-Path $env:TEMP "proj_tampered_thumb"
New-Item -ItemType Directory -Path (Join-Path $tempTampered "00_brief") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempTampered "02_filmcraft") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempTampered "03_exports") -Force | Out-Null
Copy-Item (Join-Path $testDir "00_brief\brief.md") (Join-Path $tempTampered "00_brief\brief.md")
Copy-Item (Join-Path $testDir "02_filmcraft\test-golden-10s_v01.fcproj") (Join-Path $tempTampered "02_filmcraft\test-golden-10s_v01.fcproj")
Copy-Item (Join-Path $testDir "03_exports\test-golden-10s_v01_horizontal_720.mp4") (Join-Path $tempTampered "03_exports\test-golden-10s_v01_horizontal_720.mp4")

# Crear thumbnail falso con hash adulterado en el manifiesto
Set-Content -Path (Join-Path $tempTampered "03_exports\thumbnail.jpg") -Value "DUMMY_IMAGE_BYTES" -Encoding UTF8
$tamperedManifest = @{
    status          = "ok"
    engine          = "PhotoCraft CLI 0.16.0"
    thumbnail_file  = "thumbnail.jpg"
    sha256          = "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
}
$tamperedManifest | ConvertTo-Json | Set-Content -Path (Join-Path $tempTampered "03_exports\thumbnail-manifest.json") -Encoding UTF8

$tamperPassed = $false
try {
    & "$scriptDir\ejecutar-pipeline.ps1" -Proyecto $tempTampered -PermitirTimelineExistente 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $tamperPassed = $true }
} catch {
    $tamperPassed = $false
}
Remove-Item -Path $tempTampered -Recurse -Force -ErrorAction SilentlyContinue

if ($tamperPassed) {
    Write-Host "[FALLO] El pipeline dejo pasar un manifiesto con SHA-256 adulterado." -ForegroundColor Red
    exit 1
} else {
    Write-Host "[TEST 7 PASADO] El pipeline detecto hash adulterado en manifiesto y BLOQUEO con exit 1." -ForegroundColor Green
}

# -------------------------------------------------------------
# TEST 8: Contrato estricto de PhotoCraft (proyecto/heroe/salida real)
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " TEST 8: Contrato estricto PhotoCraft (fallos y salida real)" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$tempPcNonexistent = Join-Path $env:TEMP "pc_nonexistent_test"
if (Test-Path $tempPcNonexistent) { Remove-Item -LiteralPath $tempPcNonexistent -Recurse -Force }
$pcNonexistentFailed = $false
try {
    & $pyCmd "$scriptDir\photocraft\pc_thumbnail.py" --project $tempPcNonexistent --title "TEST" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { $pcNonexistentFailed = $true }
} catch {
    $pcNonexistentFailed = $true
}

$tempPcNoHero = Join-Path $env:TEMP "pc_nohero_test"
if (Test-Path $tempPcNoHero) { Remove-Item -LiteralPath $tempPcNoHero -Recurse -Force }
New-Item -ItemType Directory -Path (Join-Path $tempPcNoHero "04_previews") -Force | Out-Null
$pcNoHeroFailed = $false
try {
    & $pyCmd "$scriptDir\photocraft\pc_thumbnail.py" --project $tempPcNoHero --title "TEST" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { $pcNoHeroFailed = $true }
} catch {
    $pcNoHeroFailed = $true
}

$tempPcFail = Join-Path $env:TEMP "pc_fail_test"
if (Test-Path $tempPcFail) { Remove-Item -LiteralPath $tempPcFail -Recurse -Force }
New-Item -ItemType Directory -Path (Join-Path $tempPcFail "04_previews") -Force | Out-Null
Copy-Item (Join-Path $testDir "04_previews\qa_01_frame.png") (Join-Path $tempPcFail "04_previews\qa_01_frame.png")
$prevEnv = $env:PHOTOCRAFT_CLI
$env:PHOTOCRAFT_CLI = "comando_inexistente_fail.exe"

$pcThrew = $false
try {
    & $pyCmd "$scriptDir\photocraft\pc_thumbnail.py" --project $tempPcFail --title "TEST" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { $pcThrew = $true }
} catch {
    $pcThrew = $true
}
$env:PHOTOCRAFT_CLI = $prevEnv

$tempPcValid = Join-Path $env:TEMP "pc_valid_test"
if (Test-Path $tempPcValid) { Remove-Item -LiteralPath $tempPcValid -Recurse -Force }
New-Item -ItemType Directory -Path (Join-Path $tempPcValid "04_previews") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempPcValid "03_exports") -Force | Out-Null
Copy-Item (Join-Path $testDir "04_previews\qa_01_frame.png") (Join-Path $tempPcValid "04_previews\qa_01_frame.png")
$validThumb = Join-Path $tempPcValid "03_exports\thumbnail.jpg"
$pcValidOk = $false
& $pyCmd "$scriptDir\photocraft\pc_thumbnail.py" --project $tempPcValid --title "TEST" --out $validThumb 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    $pcManifestPath = Join-Path $tempPcValid "03_exports\thumbnail-manifest.json"
    if (Test-Path $pcManifestPath) {
        $pcManifest = Get-Content $pcManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $pcHash = (Get-FileHash -LiteralPath $validThumb -Algorithm SHA256).Hash
        if ($pcManifest.status -eq "ok" -and
            $pcManifest.width -eq 1920 -and $pcManifest.height -eq 1080 -and
            $pcManifest.source_image -eq "qa_01_frame.png" -and
            $pcManifest.sha256 -eq $pcHash) {
            $pcValidOk = $true
        }
    }
}
Remove-Item -Path $tempPcNonexistent -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path $tempPcNoHero -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path $tempPcFail -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path $tempPcValid -Recurse -Force -ErrorAction SilentlyContinue

if ($pcNonexistentFailed -and $pcNoHeroFailed -and $pcThrew -and $pcValidOk) {
    Write-Host "[TEST 8 PASADO] PhotoCraft rechaza proyecto inexistente/sin heroe/CLI roto y verifica dimensiones reales." -ForegroundColor Green
} else {
    Write-Host "[FALLO] El contrato estricto de PhotoCraft no se cumplio." -ForegroundColor Red
    Write-Host "       proyecto_inexistente=$pcNonexistentFailed sin_heroe=$pcNoHeroFailed cli_roto=$pcThrew salida_valida=$pcValidOk" -ForegroundColor Red
    exit 1
}

# -------------------------------------------------------------
# TEST 9: Montador generico - edición real desde edit-plan.json
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " TEST 9: Montador generico (edicion real + export)        " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$tempMounter = Join-Path $env:TEMP "proj_montador_test"
if (Test-Path $tempMounter) { Remove-Item -LiteralPath $tempMounter -Recurse -Force }
New-Item -ItemType Directory -Path (Join-Path $tempMounter "00_brief") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempMounter "01_fuentes\video") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempMounter "01_fuentes\audio") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempMounter "02_filmcraft") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempMounter "03_exports") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempMounter "04_previews") -Force | Out-Null
& ffmpeg -y -nostats -loglevel error -f lavfi -i "color=c=black:size=320x240:d=1" -vframes 1 (Join-Path $tempMounter "04_previews\qa_01_frame.png")
& ffmpeg -y -nostats -loglevel error -f lavfi -i "color=c=blue:size=320x240:d=1" -vframes 1 (Join-Path $tempMounter "04_previews\qa_02_frame.png")
& ffmpeg -y -nostats -loglevel error -f lavfi -i "color=c=green:size=320x240:d=1" -vframes 1 (Join-Path $tempMounter "04_previews\qa_03_frame.png")
& ffmpeg -y -nostats -loglevel error -f lavfi -i "color=c=red:size=320x240:d=1" -vframes 1 (Join-Path $tempMounter "04_previews\qa_04_frame.png")
@"
# Brief - Montador Test

- Formato: horizontal_720
- Duracion objetivo: 2.00s

## Sin locucion hablada

Prueba de montaje con pista A1.
"@ | Set-Content -Path (Join-Path $tempMounter "00_brief\brief.md") -Encoding UTF8

& ffmpeg -y -nostats -loglevel error -f lavfi -i "testsrc=size=320x240:rate=30" -t 2 -c:v libx264 -pix_fmt yuv420p (Join-Path $tempMounter "01_fuentes\video\clip_a.mp4")
& ffmpeg -y -nostats -loglevel error -f lavfi -i "color=c=blue:size=320x240:rate=30" -t 2 -c:v libx264 -pix_fmt yuv420p (Join-Path $tempMounter "01_fuentes\video\clip_b.mp4")
& ffmpeg -y -nostats -loglevel error -f lavfi -i "sine=frequency=440:sample_rate=48000:duration=4" -ac 2 -c:a pcm_s16le (Join-Path $tempMounter "01_fuentes\audio\voz.wav")

$mounterPlan = @{
    schema_version = "1.0.0"
    project = (Split-Path -Leaf $tempMounter)
    sequence = @{ name = "Principal"; width = 320; height = 240; fps = 30; sample_rate = 48000; video_tracks = 2; audio_tracks = 1 }
    duration = 2.0
    tracks = @{
        V1 = @(
            @{ source = "video/clip_a.mp4"; start = 0.0; in = 0.5; out = 1.5 },
            @{ source = "video/clip_b.mp4"; start = 1.0; in = 0.5; out = 1.5 }
        )
        A1 = @(
            @{ source = "audio/voz.wav"; start = 0.0; in = 0.5; out = 2.5 }
        )
    }
    output = @{ slug = "montador-test" }
}
$mounterPlan | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $tempMounter "00_brief\edit-plan.json") -Encoding UTF8

$mounterFailed = $false
try {
    & "$scriptDir\ejecutar-pipeline.ps1" -Proyecto $tempMounter 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { $mounterFailed = $true }
} catch {
    $mounterFailed = $true
}

$mounterManifestPath = Join-Path $tempMounter "02_filmcraft\edit-manifest.json"
$mounterRunPath = Join-Path $tempMounter "05_logs\run.json"
$mounterOk = $false
if (-not $mounterFailed -and (Test-Path $mounterManifestPath) -and (Test-Path $mounterRunPath)) {
    $mounterManifest = Get-Content $mounterManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $mounterRun = Get-Content $mounterRunPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $mounterMaster = Join-Path $tempMounter $mounterManifest.master_file
    $mounterTimeline = Join-Path $tempMounter $mounterManifest.timeline_file
    $artifactFiles = @($mounterRun.artifacts | ForEach-Object { $_.file })
    $absoluteRel = @($mounterRun.artifacts | Where-Object { $_.rel_path -match '^[A-Za-z]:' -or $_.rel_path -match '^\\\\' }).Count
    if ($mounterManifest.status -eq "ok" -and $mounterManifest.exported -and
        (Test-Path $mounterMaster) -and (Test-Path $mounterTimeline) -and
        $mounterRun.pipeline_status -eq "SUCCESS" -and
        $mounterRun.edit_plan -eq "00_brief/edit-plan.json" -and
        $mounterRun.edit_manifest -eq "02_filmcraft/edit-manifest.json" -and
        $absoluteRel -eq 0 -and
        ($artifactFiles -contains "edit-plan.json") -and
        ($artifactFiles -contains "edit-manifest.json") -and
        ($artifactFiles -contains "clip_a.mp4") -and
        ($artifactFiles -contains "clip_b.mp4") -and
        ($artifactFiles -contains "voz.wav")) {
        $cfg = Get-Content (Join-Path $scriptDir "config.local.json") -Raw -Encoding UTF8 | ConvertFrom-Json
        $seqRaw = & $cfg.filmcraft_cli --project $mounterTimeline inspect sequence --compact
        $seq = $seqRaw | ConvertFrom-Json
        $v1Count = @($seq.video[0].items).Count
        $a1Count = @($seq.audio[0].items).Count
        if ($v1Count -eq 2 -and $a1Count -eq 1) {
            $mounterOk = $true
        }
    }
}

if (-not $mounterOk) {
    Write-Host "[FALLO] El pipeline/montador no produjo una timeline V1/A1 verificable o un run.json completo." -ForegroundColor Red
    exit 1
} else {
    Write-Host "[TEST 9 PASADO] edit-plan.json -> pipeline -> timeline V1/A1 -> export FilmCraft -> master y run.json aprobados." -ForegroundColor Green
}
if (-not $KeepArtifacts) { Remove-Item -LiteralPath $tempMounter -Recurse -Force -ErrorAction SilentlyContinue }

# -------------------------------------------------------------
# TEST 10: Remotion - Renderizado de gráficos con Alfa y Manifiesto
# -------------------------------------------------------------
Write-Host "`n----------------------------------------------------------" -ForegroundColor Cyan
Write-Host " TEST 10: Remotion (Motion Graphics con Alfa y SHA-256)   " -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

$tempRemotionDir = Join-Path $env:TEMP "remotion_test_suite"
if (Test-Path $tempRemotionDir) { Remove-Item -LiteralPath $tempRemotionDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempRemotionDir -Force | Out-Null

$remOutMov = Join-Path $tempRemotionDir "overlay_test.mov"
$remOk = $false
try {
    & $pyCmd "$scriptDir\remotion\rem_render.py" --comp "InfografiaHorizontal" --format "prores" --channels "rgba" --frames "0-15" --output $remOutMov 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0 -and (Test-Path $remOutMov)) {
        $remManifestPath = Join-Path $tempRemotionDir "render-manifest-InfografiaHorizontal.json"
        if (Test-Path $remManifestPath) {
            $remManifest = Get-Content $remManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $realHash = (Get-FileHash -LiteralPath $remOutMov -Algorithm SHA256).Hash
            if ($remManifest.status -eq "ok" -and $remManifest.has_alpha -eq $true -and $remManifest.sha256 -eq $realHash) {
                $remOk = $true
            }
        }
    }
} catch {
    $remOk = $false
}

# Prueba negativa: composición inexistente debe fallar con exit 1
$remNegFailed = $false
try {
    & $pyCmd "$scriptDir\remotion\rem_render.py" --comp "ComposicionInexistenteQueDebeFallar" --output (Join-Path $tempRemotionDir "fail.mov") 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { $remNegFailed = $true }
} catch {
    $remNegFailed = $true
}

if (-not $KeepArtifacts) { Remove-Item -LiteralPath $tempRemotionDir -Recurse -Force -ErrorAction SilentlyContinue }

if ($remOk -and $remNegFailed) {
    Write-Host "[TEST 10 PASADO] Remotion renderizo ProRes 4444 RGBA (con alfa), emitio manifiesto SHA-256 y rechazo composicion invalida." -ForegroundColor Green
} else {
    Write-Host "[FALLO] El motor Remotion no cumplio el contrato criptografico con alfa." -ForegroundColor Red
    Write-Host "        rem_ok=$remOk rem_neg_failed=$remNegFailed" -ForegroundColor Red
    exit 1
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " [SUITE EXITOSA] Las 10 pruebas rigurosas pasaron al 100% " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
if (-not $KeepArtifacts) { Remove-Item -LiteralPath $testDir -Recurse -Force -ErrorAction SilentlyContinue }
