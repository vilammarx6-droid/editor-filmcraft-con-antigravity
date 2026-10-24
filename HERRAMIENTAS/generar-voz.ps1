param(
    [Parameter(Mandatory = $true)]
    [string]$Proyecto,

    [Parameter(Mandatory = $false)]
    [string]$Texto,

    [Parameter(Mandatory = $false)]
    [string]$Voz = "es-PE-AlexNeural",

    [Parameter(Mandatory = $false)]
    [string]$NombreSalida = "locucion"
)

$ErrorActionPreference = "Stop"

$workspaceRoot = Split-Path -Parent $PSScriptRoot

# Resolver carpeta de proyecto
if (-not (Test-Path -LiteralPath $Proyecto)) {
    $posible = Join-Path $workspaceRoot $Proyecto
    if (Test-Path -LiteralPath $posible) {
        $Proyecto = $posible
    } else {
        throw "No se encontró el proyecto en: $Proyecto"
    }
}

$briefPath = Join-Path $Proyecto "00_brief\brief.md"
$destAudio = Join-Path $Proyecto "01_fuentes\audio"

if (-not (Test-Path -LiteralPath $destAudio)) {
    New-Item -ItemType Directory -Path $destAudio -Force | Out-Null
}

# Si no se pasó texto, intentar extraerlo del brief
if (-not $Texto -or $Texto.Trim() -eq "") {
    if (Test-Path -LiteralPath $briefPath) {
        $briefContent = Get-Content -LiteralPath $briefPath -Raw
        if ($briefContent -match "(?ms)## Guion\s*\r?\n(.*?)(?=\r?\n##|\Z)") {
            $Texto = $matches[1].Trim()
        } elseif ($briefContent -match "(?m)^-\s*Guion:\s*(.+)$") {
            $Texto = $matches[1].Trim()
        } elseif ($briefContent -match "(?ms)## Estructura\s*\r?\n(.*?)(?=\r?\n##|\Z)") {
            $Texto = $matches[1].Trim()
        }
    }
}

if (-not $Texto -or $Texto.Trim() -eq "") {
    throw "No se proporcionó texto y no se encontró una sección de guion en $briefPath."
}

Write-Host "=== Generando locución con Edge-TTS (Voz: $Voz) ===" -ForegroundColor Cyan
Write-Host "Texto a locutar:`n$Texto`n" -ForegroundColor Gray

$tempMp3 = Join-Path $env:TEMP "$($NombreSalida)_$([Guid]::NewGuid().ToString().Substring(0,8)).mp3"
$tempVtt = Join-Path $env:TEMP "$($NombreSalida)_$([Guid]::NewGuid().ToString().Substring(0,8)).vtt"
$finalWav = Join-Path $destAudio "$($NombreSalida).wav"
$finalSrt = Join-Path $destAudio "$($NombreSalida).srt"
$finalVtt = Join-Path $destAudio "$($NombreSalida).vtt"

try {
    # 1. Generar audio y subtítulos con edge-tts
    & edge-tts --voice $Voz --text $Texto --write-media $tempMp3 --write-subtitles $tempVtt
    if (-not (Test-Path -LiteralPath $tempMp3)) {
        throw "Error: no se generó el archivo de audio con edge-tts."
    }

    # 2. Convertir a WAV 48 kHz Estéreo (estándar nativo de FilmCraft)
    Write-Host "Convirtiendo a WAV 48kHz estéreo para FilmCraft..." -ForegroundColor Gray
    $prevEA = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & ffmpeg -y -loglevel error -i $tempMp3 -ar 48000 -ac 2 $finalWav
    
    # 3. Guardar subtítulos en VTT y SRT
    if (Test-Path -LiteralPath $tempVtt) {
        Copy-Item -LiteralPath $tempVtt -Destination $finalVtt -Force
        & ffmpeg -y -loglevel error -i $tempVtt $finalSrt
    }
    $ErrorActionPreference = $prevEA

    if (-not (Test-Path -LiteralPath $finalWav)) {
        throw "Error al convertir audio a WAV."
    }

    Write-Host "¡Locución generada exitosamente!" -ForegroundColor Green
    Write-Host "  Audio (WAV 48kHz): $finalWav" -ForegroundColor Green
    if (Test-Path -LiteralPath $finalSrt) {
        Write-Host "  Subtítulos (SRT):  $finalSrt" -ForegroundColor Green
    }
    Write-Host "`nListo para importar al timeline de FilmCraft." -ForegroundColor Cyan
} finally {
    if (Test-Path -LiteralPath $tempMp3) { Remove-Item -LiteralPath $tempMp3 -Force -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $tempVtt) { Remove-Item -LiteralPath $tempVtt -Force -ErrorAction SilentlyContinue }
}
