param(
    [Parameter(Mandatory = $true)]
    [string]$Proyecto,

    [Parameter(Mandatory = $false)]
    [ValidateSet("musica", "sfx", "graficos", "cultural", "memes", "todos")]
    [string]$Tipo = "todos",

    [Parameter(Mandatory = $false)]
    [string]$Filtro = "*"
)

$ErrorActionPreference = "Stop"

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$recursosRoot = Join-Path $workspaceRoot "RECURSOS_COMPARTIDOS"

# Resolver carpeta de proyecto
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

    if ($hallado) {
        $Proyecto = $hallado
    } else {
        throw "No se encontró el proyecto en: $Proyecto"
    }
}

$destMusica   = Join-Path $Proyecto "01_fuentes\musica"
$destAudio    = Join-Path $Proyecto "01_fuentes\audio"
$destGraficos = Join-Path $Proyecto "01_fuentes\graficos"
$destVideo    = Join-Path $Proyecto "01_fuentes\video"

if (-not (Test-Path -LiteralPath $destMusica))   { New-Item -ItemType Directory -Path $destMusica   -Force | Out-Null }
if (-not (Test-Path -LiteralPath $destAudio))    { New-Item -ItemType Directory -Path $destAudio    -Force | Out-Null }
if (-not (Test-Path -LiteralPath $destGraficos)) { New-Item -ItemType Directory -Path $destGraficos -Force | Out-Null }
if (-not (Test-Path -LiteralPath $destVideo))    { New-Item -ItemType Directory -Path $destVideo    -Force | Out-Null }

Write-Host "=== Importando recursos libres (Tipo: $Tipo | Filtro: '$Filtro') a $Proyecto ===" -ForegroundColor Cyan

# Función auxiliar para filtrar por nombre
function Coincide-Filtro($nombreArchivo, $patron) {
    if ([string]::IsNullOrWhiteSpace($patron) -or $patron -eq "*") { return $true }
    foreach ($p in ($patron -split ",")) {
        $limpio = $p.Trim()
        if ($nombreArchivo -like "*$limpio*") { return $true }
    }
    return $false
}

$copiados = 0

# 1. Música General
if ($Tipo -eq "musica" -or $Tipo -eq "todos") {
    $origenMusica = Join-Path $recursosRoot "01_musica"
    if (Test-Path -LiteralPath $origenMusica) {
        $tracks = Get-ChildItem -LiteralPath $origenMusica -File -Filter "*.mp3" | Where-Object { Coincide-Filtro $_.Name $Filtro }
        foreach ($t in $tracks) {
            Copy-Item -LiteralPath $t.FullName -Destination $destMusica -Force
            Write-Host "  [Música] $($t.Name) -> 01_fuentes\musica" -ForegroundColor Green
            $copiados++
        }
    }
}

# 2. Efectos de sonido (SFX Generales)
if ($Tipo -eq "sfx" -or $Tipo -eq "todos") {
    $origenSfx = Join-Path $recursosRoot "02_efectos_sonido"
    if (Test-Path -LiteralPath $origenSfx) {
        $sfxs = Get-ChildItem -LiteralPath $origenSfx -File -Filter "*.wav" | Where-Object { Coincide-Filtro $_.Name $Filtro }
        foreach ($s in $sfxs) {
            Copy-Item -LiteralPath $s.FullName -Destination $destAudio -Force
            Write-Host "  [SFX] $($s.Name) -> 01_fuentes\audio" -ForegroundColor Yellow
            $copiados++
        }
    }
}

# 3. Recursos Culturales (Cusco, Chumbivilcas, Santoto, Wakawaqra)
if ($Tipo -eq "cultural" -or $Tipo -eq "todos") {
    $origenCultural = Join-Path $recursosRoot "02_efectos_sonido\cultural_cusco_chumbivilcas"
    if (Test-Path -LiteralPath $origenCultural) {
        $cults = Get-ChildItem -LiteralPath $origenCultural -File -Filter "*.wav" | Where-Object { Coincide-Filtro $_.Name $Filtro }
        foreach ($c in $cults) {
            Copy-Item -LiteralPath $c.FullName -Destination $destAudio -Force
            Write-Host "  [Cultural Cusco/Chumbivilcas] $($c.Name) -> 01_fuentes\audio" -ForegroundColor DarkYellow
            $copiados++
        }
    }
}

# 4. Recursos Virales y Memes (Audio y SFX)
if ($Tipo -eq "memes" -or $Tipo -eq "todos") {
    $origenMemesMus = Join-Path $recursosRoot "01_musica\memes_y_virales"
    if (Test-Path -LiteralPath $origenMemesMus) {
        $mmus = Get-ChildItem -LiteralPath $origenMemesMus -File -Filter "*.mp3" | Where-Object { Coincide-Filtro $_.Name $Filtro }
        foreach ($m in $mmus) {
            Copy-Item -LiteralPath $m.FullName -Destination $destMusica -Force
            Write-Host "  [Meme Música] $($m.Name) -> 01_fuentes\musica" -ForegroundColor Cyan
            $copiados++
        }
    }
    $origenMemesSfx = Join-Path $recursosRoot "02_efectos_sonido\memes_y_virales"
    if (Test-Path -LiteralPath $origenMemesSfx) {
        $msfx = Get-ChildItem -LiteralPath $origenMemesSfx -File -Filter "*.wav" | Where-Object { Coincide-Filtro $_.Name $Filtro }
        foreach ($s in $msfx) {
            Copy-Item -LiteralPath $s.FullName -Destination $destAudio -Force
            Write-Host "  [Meme SFX] $($s.Name) -> 01_fuentes\audio" -ForegroundColor Cyan
            $copiados++
        }
    }
}

# 5. Gráficos, Stickers, Overlays y Pantallas Verdes
if ($Tipo -eq "graficos" -or $Tipo -eq "todos") {
    $origenGraficos = Join-Path $recursosRoot "03_animaciones_y_graficos"
    if (Test-Path -LiteralPath $origenGraficos) {
        # Copiar imágenes PNG a graficos
        $imgs = Get-ChildItem -LiteralPath $origenGraficos -Recurse -File -Filter "*.png" | Where-Object { Coincide-Filtro $_.Name $Filtro }
        foreach ($img in $imgs) {
            Copy-Item -LiteralPath $img.FullName -Destination $destGraficos -Force
            Write-Host "  [Gráfico] $($img.Name) -> 01_fuentes\graficos" -ForegroundColor Magenta
            $copiados++
        }
        # Copiar videos de pantalla verde a video
        $vids = Get-ChildItem -LiteralPath $origenGraficos -Recurse -File -Filter "*.mp4" | Where-Object { Coincide-Filtro $_.Name $Filtro }
        foreach ($vid in $vids) {
            Copy-Item -LiteralPath $vid.FullName -Destination $destVideo -Force
            Write-Host "  [Pantalla Verde] $($vid.Name) -> 01_fuentes\video" -ForegroundColor DarkCyan
            $copiados++
        }
    }
}

Write-Host "`nImportación completada ($copiados archivos copiados). Ahora puedes usar media_import o filmcraft-cli import." -ForegroundColor Cyan
