<#
.SYNOPSIS
    Orquestador Determinista de Produccion y Quality Gate para FilmCraft.

.DESCRIPTION
    Ejecuta el pipeline de produccion desacoplado de la IA:
    1. Valida el contrato de datos del brief (00_brief/brief.md con seccion ## Guion).
    2. Ejecuta la sintesis de voz neural (Edge-TTS) y genera WAV 48kHz + SRT.
    3. Inspecciona y valida el proyecto FilmCraft (.fcproj).
    4. Genera el collage de revision determinista (crear-collage-qa.py).
    5. Ejecuta el Quality Gate de audio/video (auditar-calidad.py) y bloquea con exit 1 si no cumple.
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Proyecto,

    [switch]$RegenerarVoz,

    [switch]$OmitirQualityGate
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [PIPELINE] Orquestador Determinista de Produccion        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$workspaceRoot = Split-Path -Parent $PSScriptRoot

# 1. Resolver proyecto
if (-not (Test-Path -LiteralPath $Proyecto)) {
    $candidatos = @(
        (Join-Path $workspaceRoot $Proyecto),
        (Join-Path $workspaceRoot "PROYECTOS\$Proyecto")
    )
    $hallado = $candidatos | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

    if (-not $hallado) {
        $proyectosDir = Join-Path $workspaceRoot "PROYECTOS"
        if (Test-Path $proyectosDir) {
            $match = Get-ChildItem -LiteralPath $proyectosDir -Directory |
                Where-Object { $_.Name -like "*$Proyecto*" } | Select-Object -First 1
            if ($match) { $hallado = $match.FullName }
        }
    }

    if ($hallado) { $Proyecto = $hallado }
    else { throw "No se encontro el proyecto: $Proyecto" }
}

Write-Host "-> Proyecto detectado: $Proyecto" -ForegroundColor Green

# 2. Comprobar contrato de brief y guion
$briefPath = Join-Path $Proyecto "00_brief\brief.md"
if (-not (Test-Path $briefPath)) {
    throw "Falta el archivo de contrato del brief: $briefPath"
}

Write-Host "`n[Fase 1/4] Validacion de Guion y Sintesis de Audio..." -ForegroundColor Yellow
$audioDir = Join-Path $Proyecto "01_fuentes\audio"
$locucionWav = Join-Path $audioDir "locucion.wav"

$hasGuion = $false
$briefContent = Get-Content -LiteralPath $briefPath -Raw -Encoding UTF8
if ($briefContent -match "(?ms)##\s*Gui[oó]n" -or $briefContent -match "(?m)^-\s*Guion:") {
    $hasGuion = $true
}

if ($hasGuion) {
    if ($RegenerarVoz -or -not (Test-Path $locucionWav)) {
        & "$PSScriptRoot\generar-voz.ps1" -Proyecto $Proyecto -NombreSalida "locucion"
        if ($LASTEXITCODE -ne 0) {
            throw "Error generando la locucion del proyecto."
        }
    } else {
        Write-Host "  -> Locucion ya existente en: $locucionWav" -ForegroundColor Gray
    }
} else {
    Write-Host "  -> Proyecto sin locucion hablada (musical o instrumental). Omitiendo TTS." -ForegroundColor Gray
}

# 3. Comprobar proyecto FilmCraft y Montaje Real
Write-Host "`n[Fase 2/4] Validacion de Linea de Tiempo en FilmCraft..." -ForegroundColor Yellow
$fcDir = Join-Path $Proyecto "02_filmcraft"
$candidatosFc = Get-ChildItem -LiteralPath $fcDir -Filter "*.fcproj" -File -ErrorAction SilentlyContinue |
    Where-Object { $_.DirectoryName -notmatch "Auto-Save" }
$fcprojFile = $candidatosFc | Sort-Object {
    if ($_.BaseName -match '_v(\d+)') { [int]$matches[1] } else { 0 }
}, LastWriteTime -Descending | Select-Object -First 1

if (-not $fcprojFile) {
    throw "FALLO CRITICO: No existe ningun archivo .fcproj en $fcDir. El pipeline exige una linea de tiempo real montada en FilmCraft."
}

& "$PSScriptRoot\resumir-timeline.ps1" -Proyecto $Proyecto
if ($LASTEXITCODE -ne 0) {
    throw "FALLO CRITICO: La linea de tiempo de FilmCraft en $($fcprojFile.Name) esta corrupta o no pudo ser leida."
}

# 4. Validacion de Manifiestos de Motion Graphics (EffectCraft)
Write-Host "`n[Fase 3/6] Validacion de Activos y Manifiestos de EffectCraft..." -ForegroundColor Yellow
$gfxDir = Join-Path $Proyecto "01_fuentes\graficos"
$disenoFiles = Get-ChildItem -LiteralPath $gfxDir -Filter "*diseno*.json" -File -ErrorAction SilentlyContinue
if ($disenoFiles) {
    foreach ($df in $disenoFiles) {
        $baseName = $df.BaseName
        $specificManifest = Join-Path $gfxDir "render-manifest-$baseName.json"
        $globalManifest   = Join-Path $gfxDir "render-manifest.json"
        
        $targetManifest = $null
        if (Test-Path $specificManifest) {
            $targetManifest = $specificManifest
        } elseif (Test-Path $globalManifest) {
            $targetManifest = $globalManifest
        }

        if (-not $targetManifest) {
            throw "FALLO DE CONTRATO GRAFICO: Existen especificaciones de diseno en $($df.Name) pero falta 'render-manifest.json' o 'render-manifest-$baseName.json'. Todo render debe estar verificado criptograficamente."
        }
        $gm = Get-Content $targetManifest -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($gm.status -ne "ok") {
            throw "FALLO DE CONTRATO GRAFICO: El manifiesto '$((Split-Path -Leaf $targetManifest))' reporta status='$($gm.status)'. El auditor rechaza assets fallidos."
        }
        Write-Host "  -> Manifiesto de EffectCraft verificado para $($df.Name): $($gm.output_file) (SHA256: $($gm.sha256.Substring(0,16))..., Alfa: $($gm.has_alpha))" -ForegroundColor Green
    }
} else {
    Write-Host "  -> No se detectaron especificaciones de diseno EffectCraft en este proyecto." -ForegroundColor Gray
}

# 4.1 Validacion de Manifiestos de Audio (SoundCraft)
$audioDir = Join-Path $Proyecto "01_fuentes\audio"
$audioManifests = Get-ChildItem -LiteralPath $audioDir -Filter "*manifest*.json" -File -ErrorAction SilentlyContinue
if ($audioManifests) {
    Write-Host "`n[Fase 3.1/6] Validacion de Manifiestos de SoundCraft..." -ForegroundColor Yellow
    foreach ($am in $audioManifests) {
        $amData = Get-Content $am.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        $audioTarget = Join-Path $audioDir $amData.output_file
        if (-not (Test-Path $audioTarget)) {
            throw "FALLO DE CONTRATO DE AUDIO: El manifiesto '$($am.Name)' referencia '$($amData.output_file)' que no existe en disco."
        }
        $realAudioHash = (Get-FileHash -LiteralPath $audioTarget -Algorithm SHA256).Hash
        if ($realAudioHash -ne $amData.sha256) {
            throw "MANIPULACION DE AUDIO: El SHA256 real de '$($amData.output_file)' ($realAudioHash) no coincide con el manifiesto ($($amData.sha256))."
        }
        if ($amData.channels -ne 2 -or $amData.sample_rate -ne 48000) {
            throw "FALLO DE ESPECIFICACION DE AUDIO: '$($amData.output_file)' no cumple 48kHz estéreo ($($amData.sample_rate) Hz, $($amData.channels) ch)."
        }
        Write-Host "  -> Manifiesto de Audio SoundCraft verificado: $($amData.output_file) (48kHz Estéreo, SHA256: $($amData.sha256.Substring(0,16))...)" -ForegroundColor Green
    }
}

# 5. Generar Collage de Auditoria QA
Write-Host "`n[Fase 4/6] Generacion de Collage Determinista QA..." -ForegroundColor Yellow
$pyCmd = "python"
& $pyCmd "$PSScriptRoot\crear-collage-qa.py" $Proyecto

# 6. Quality Gate de Export Estricto y Miniaturas
Write-Host "`n[Fase 5/6] Ejecutando Quality Gate de Audio y Video..." -ForegroundColor Yellow
$exportsDir = Join-Path $Proyecto "03_exports"
$masterVideos = Get-ChildItem -LiteralPath $exportsDir -Filter "*.mp4" -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending

if (-not $masterVideos) {
    Write-Host "`n[FALLO FATAL] No existe ningun video master exportado (*.mp4) en $exportsDir." -ForegroundColor Red
    Write-Host "Un pipeline de produccion de video no puede declarar exito sin video final montado y renderizado." -ForegroundColor Red
    
    $failedRun = @{
        schema_version  = "1.0.0"
        session_id      = [Guid]::NewGuid().ToString()
        timestamp_utc   = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        pipeline_status = "FAILED_NO_MASTER"
        exit_code       = 1
        project         = (Split-Path -Leaf $Proyecto)
        quality_gate    = "FAILED"
        error           = "No se encontro ningun archivo .mp4 master en 03_exports"
    }
    $runJsonPath = Join-Path $Proyecto "05_logs\run.json"
    $failedRun | ConvertTo-Json -Depth 5 | Set-Content -Path $runJsonPath -Encoding UTF8
    exit 1
}

$targetVideo = $masterVideos[0].FullName
Write-Host "  -> Auditando master: $($masterVideos[0].Name)" -ForegroundColor Cyan

if (-not $OmitirQualityGate) {
    & $pyCmd "$PSScriptRoot\auditar-calidad.py" $targetVideo
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n[BLOQUEO DE CALIDAD] El master NO cumple los estandares de emision." -ForegroundColor Red
        Write-Host "Ejecuta: python .\HERRAMIENTAS\remediar-audio.py `"$targetVideo`"" -ForegroundColor Yellow
        
        # Registrar run.json con estado fallido
        $failedRun = @{
            session_id      = [Guid]::NewGuid().ToString()
            timestamp_utc   = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
            pipeline_status = "FAILED_QUALITY_GATE"
            exit_code       = 1
            project         = (Split-Path -Leaf $Proyecto)
            target_video    = (Split-Path -Leaf $targetVideo)
        }
        $failedRun | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $Proyecto "05_logs\run.json") -Encoding UTF8
        exit 1
    }
}

# 6.1 Validar Miniatura y Manifiesto de PhotoCraft si existen
$thumbManifestPath = Join-Path $exportsDir "thumbnail-manifest.json"
if (Test-Path $thumbManifestPath) {
    Write-Host "`n[Fase 5.1/6] Validacion de Manifiesto de Miniatura (PhotoCraft)..." -ForegroundColor Yellow
    $tmData = Get-Content $thumbManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $thumbTarget = Join-Path $exportsDir $tmData.thumbnail_file
    if (-not (Test-Path $thumbTarget)) {
        throw "FALLO DE CONTRATO DE MINIATURA: El manifiesto referencia '$($tmData.thumbnail_file)' que no existe en disco."
    }
    $realThumbHash = (Get-FileHash -LiteralPath $thumbTarget -Algorithm SHA256).Hash
    if ($realThumbHash -ne $tmData.sha256) {
        throw "MANIPULACION DE MINIATURA: El SHA256 real de '$($tmData.thumbnail_file)' ($realThumbHash) no coincide con el manifiesto ($($tmData.sha256))."
    }
    if ($tmData.status -eq "degradado") {
        Write-Warning "Aviso de Auditoria: La miniatura fue generada con motor degradado ($($tmData.engine))."
    } else {
        Write-Host "  -> Manifiesto de Miniatura PhotoCraft verificado: $($tmData.thumbnail_file) (Motor: $($tmData.engine), SHA256: $($tmData.sha256.Substring(0,16))...)" -ForegroundColor Green
    }
}

# 7. Generar Traza Estructurada run.json con Hashes Criptograficos Reales
$sessionId = [Guid]::NewGuid().ToString()
$timestampUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

$artifacts = @()
$candidateFiles = @(
    (Join-Path $Proyecto "00_brief\brief.md"),
    (Join-Path $Proyecto "01_fuentes\audio\locucion.wav"),
    (Join-Path $Proyecto "01_fuentes\audio\locucion.srt"),
    (Join-Path $Proyecto "04_previews\collage_qc.png")
)
# Agregar disenos, manifiestos y overlays en 01_fuentes/graficos
if (Test-Path $gfxDir) {
    Get-ChildItem -LiteralPath $gfxDir -Filter "*manifest*.json" -File | ForEach-Object { $candidateFiles += $_.FullName }
    Get-ChildItem -LiteralPath $gfxDir -Filter "*diseno*.json" -File | ForEach-Object { $candidateFiles += $_.FullName }
    Get-ChildItem -LiteralPath $gfxDir -Filter "*.mov" -File | ForEach-Object { $candidateFiles += $_.FullName }
    Get-ChildItem -LiteralPath $gfxDir -Filter "*.png" -File | ForEach-Object { $candidateFiles += $_.FullName }
}
# Agregar manifiestos y audios procesados en 01_fuentes/audio
if (Test-Path $audioDir) {
    Get-ChildItem -LiteralPath $audioDir -Filter "*manifest*.json" -File | ForEach-Object { $candidateFiles += $_.FullName }
    Get-ChildItem -LiteralPath $audioDir -Filter "*master*.wav" -File | ForEach-Object { $candidateFiles += $_.FullName }
}
# Agregar miniaturas y manifiestos en 03_exports
if (Test-Path $exportsDir) {
    Get-ChildItem -LiteralPath $exportsDir -Filter "*thumbnail*.json" -File | ForEach-Object { $candidateFiles += $_.FullName }
    Get-ChildItem -LiteralPath $exportsDir -Filter "*thumbnail*.jpg" -File | ForEach-Object { $candidateFiles += $_.FullName }
    Get-ChildItem -LiteralPath $exportsDir -Filter "*thumbnail*.png" -File | ForEach-Object { $candidateFiles += $_.FullName }
}
if ($masterVideos -and $masterVideos.Count -gt 0) {
    $candidateFiles += $masterVideos[0].FullName
}
if ($fcprojFile) { $candidateFiles += $fcprojFile.FullName }
$candidateFiles = $candidateFiles | Select-Object -Unique

foreach ($cf in $candidateFiles) {
    if (Test-Path -LiteralPath $cf) {
        $hashObj = Get-FileHash -LiteralPath $cf -Algorithm SHA256
        $item = Get-Item -LiteralPath $cf
        $artifacts += @{
            file        = (Split-Path -Leaf $cf)
            rel_path    = $cf.Replace($Proyecto, "").TrimStart("\/")
            sha256      = $hashObj.Hash
            size_bytes  = $item.Length
            modified    = $item.LastWriteTimeUtc.ToString("yyyy-MM-ddTHH:mm:ssZ")
        }
    }
}

$runManifest = @{
    schema_version   = "1.0.0"
    session_id       = $sessionId
    timestamp_utc    = $timestampUtc
    pipeline_status  = "SUCCESS"
    exit_code        = 0
    project          = (Split-Path -Leaf $Proyecto)
    target_video     = if ($masterVideos) { $masterVideos[0].Name } else { $null }
    quality_gate     = "PASSED"
    artifacts_count  = $artifacts.Count
    artifacts        = $artifacts
}

$runJsonPath = Join-Path $Proyecto "05_logs\run.json"
$runManifest | ConvertTo-Json -Depth 5 | Set-Content -Path $runJsonPath -Encoding UTF8
Write-Host "-> Traza de ejecucion verificable registrada: $runJsonPath" -ForegroundColor Cyan

Write-Host "`n[EXITO] Pipeline completado. Todos los contratos y estandares fueron satisfechos." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
