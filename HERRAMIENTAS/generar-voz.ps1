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

# Resolver carpeta de proyecto de forma resiliente
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
    else { throw "No se encontró el proyecto en: $Proyecto" }
}

$briefPath = Join-Path $Proyecto "00_brief\brief.md"
$destAudio = Join-Path $Proyecto "01_fuentes\audio"

if (-not (Test-Path -LiteralPath $destAudio)) {
    New-Item -ItemType Directory -Path $destAudio -Force | Out-Null
}

# Si no se pasó texto, intentar extraerlo del brief con regex flexible de cuerpo
if (-not $Texto -or $Texto.Trim() -eq "") {
    if (Test-Path -LiteralPath $briefPath) {
        $briefContent = Get-Content -LiteralPath $briefPath -Raw -Encoding UTF8
        
        # 1. Extraer sección de Guion o Locución hasta el siguiente encabezado H2 (## )
        if ($briefContent -match '(?si)##\s*(?:Gui.*?n|Locuci.*?n)[^\r\n]*\r?\n([\s\S]+)') {
            $cuerpo = $matches[1]
            $partes = $cuerpo -split '(?m)^\s*##\s+'
            $Texto = $partes[0].Trim()
        } elseif ($briefContent -match "(?m)^-\s*Guion:\s*(.+)$") {
            $Texto = $matches[1].Trim()
        } elseif ($briefContent -match '(?si)##\s*Estructura[^\r\n]*\r?\n([\s\S]+)') {
            $cuerpo = $matches[1]
            $partes = $cuerpo -split '(?m)^\s*##\s+'
            $Texto = $partes[0].Trim()
        }

        # Limpiar notas de producción, encabezados H3 (### Escena...), viñetas y formato Markdown
        if ($Texto) {
            $Texto = $Texto -replace '(?s)<!--.*?-->', ''
            $Texto = $Texto -replace '(?m)^\s*###[^\r\n]*', '' # remover títulos de escenas H3
            $Texto = $Texto -replace '(?m)^\s*>\s*', ''        # remover quotes de markdown >
            $Texto = $Texto -replace '[*_`~"]', ''             # remover marcas de estilo markdown
            $Texto = $Texto.Trim()
        }
    }
}

if (-not $Texto -or $Texto.Trim() -eq "") {
    throw "No se proporcionó texto y no se encontró una sección de guion en $briefPath."
}

Write-Host "=== Generando locución con Edge-TTS (Voz: $Voz) ===" -ForegroundColor Cyan
Write-Host "Texto a locutar:`n$Texto`n" -ForegroundColor Gray

$tempTxt = Join-Path $env:TEMP "$($NombreSalida)_$([Guid]::NewGuid().ToString().Substring(0,8)).txt"
$tempMp3 = Join-Path $env:TEMP "$($NombreSalida)_$([Guid]::NewGuid().ToString().Substring(0,8)).mp3"
$tempVtt = Join-Path $env:TEMP "$($NombreSalida)_$([Guid]::NewGuid().ToString().Substring(0,8)).vtt"
$finalWav = Join-Path $destAudio "$($NombreSalida).wav"
$finalSrt = Join-Path $destAudio "$($NombreSalida).srt"
$finalVtt = Join-Path $destAudio "$($NombreSalida).vtt"

try {
    # 1. Escribir texto a archivo temporal UTF-8 para evitar desbordamiento CLI en Windows (>8191 caracteres)
    [System.IO.File]::WriteAllText($tempTxt, $Texto, [System.Text.Encoding]::UTF8)

    # 2. Generar audio y subtítulos con edge-tts mediante --file
    & edge-tts --voice $Voz --file $tempTxt --write-media $tempMp3 --write-subtitles $tempVtt
    if (-not (Test-Path -LiteralPath $tempMp3)) {
        throw "Error: no se generó el archivo de audio con edge-tts."
    }

    # 3. Convertir a WAV 48 kHz Estéreo (estándar nativo de FilmCraft)
    Write-Host "Convirtiendo a WAV 48kHz estéreo para FilmCraft..." -ForegroundColor Gray
    $prevEA = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & ffmpeg -y -loglevel error -i $tempMp3 -ar 48000 -ac 2 $finalWav
    
    # 4. Guardar subtítulos en VTT y SRT
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
    if (Test-Path -LiteralPath $tempTxt) { Remove-Item -LiteralPath $tempTxt -Force -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $tempMp3) { Remove-Item -LiteralPath $tempMp3 -Force -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $tempVtt) { Remove-Item -LiteralPath $tempVtt -Force -ErrorAction SilentlyContinue }
}
