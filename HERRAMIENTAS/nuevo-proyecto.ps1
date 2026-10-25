param(
  [Parameter(Mandatory=$true)]
  [string]$Nombre,

  [ValidateSet("vertical_1080","horizontal_1080","cuadrado_1080","cine_1080_24","vertical_720","horizontal_720","vertical_480","horizontal_480","vertical_420","horizontal_420")]
  [string]$Formato = "vertical_720"
)

$ErrorActionPreference = "Stop"

$Root = "C:\Users\marx_\OneDrive\Documentos\Proyecto predeterminado\EditorVideo"
$Cli  = "C:\Users\marx_\.gemini\antigravity\scratch\craft_tools\filmcraft\filmcraft-0.9.0-windows-x64-portable\filmcraft-cli.exe"

$Formatos = @{
  "vertical_1080"   = @{ W = 1080; H = 1920; FPS = 30; Nombre = "Vertical 1080p" }
  "horizontal_1080" = @{ W = 1920; H = 1080; FPS = 30; Nombre = "Horizontal 1080p" }
  "cuadrado_1080"   = @{ W = 1080; H = 1080; FPS = 30; Nombre = "Cuadrado 1080p" }
  "cine_1080_24"    = @{ W = 1920; H = 1080; FPS = 24; Nombre = "Cine 1080p 24fps" }
  "vertical_720"    = @{ W = 720;  H = 1280; FPS = 30; Nombre = "Vertical 720p" }
  "horizontal_720"  = @{ W = 1280; H = 720;  FPS = 30; Nombre = "Horizontal 720p" }
  "vertical_480"    = @{ W = 480;  H = 854;  FPS = 30; Nombre = "Vertical 480p" }
  "horizontal_480"  = @{ W = 854;  H = 480;  FPS = 30; Nombre = "Horizontal 480p" }
  "vertical_420"    = @{ W = 420;  H = 746;  FPS = 30; Nombre = "Vertical 420p" }
  "horizontal_420"  = @{ W = 746;  H = 420;  FPS = 30; Nombre = "Horizontal 420p" }
}

$Fecha = Get-Date -Format "yyyy-MM-dd"
$Slug = $Nombre.Normalize([Text.NormalizationForm]::FormD)
$Slug = -join ($Slug.ToCharArray() | Where-Object { [Globalization.CharUnicodeInfo]::GetUnicodeCategory($_) -ne [Globalization.UnicodeCategory]::NonSpacingMark })
$Slug = $Slug.ToLower() -replace "[^a-z0-9]+", "-"
$Slug = $Slug.Trim("-")
if ([string]::IsNullOrWhiteSpace($Slug)) { throw "Nombre invalido." }

$Proyecto = Join-Path $Root "PROYECTOS\$Fecha`_$Slug"
if (Test-Path $Proyecto) { throw "Ya existe: $Proyecto" }

$Subcarpetas = @(
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

foreach ($sub in $Subcarpetas) {
  New-Item -ItemType Directory -Path (Join-Path $Proyecto $sub) -Force | Out-Null
}

$f = $Formatos[$Formato]
$brief = Get-Content (Join-Path $Root "_PLANTILLA\brief.md") -Raw
$brief = $brief.Replace("{{NOMBRE}}", $Nombre)
$brief = $brief.Replace("{{FECHA}}", $Fecha)
$brief = $brief.Replace("{{FORMATO}}", $Formato)
$brief = $brief.Replace("{{RESOLUCION}}", "$($f.W)x$($f.H)")
Set-Content -Path (Join-Path $Proyecto "00_brief\brief.md") -Value $brief -Encoding UTF8

$log = "# Edit log - $Nombre`n`n- $Fecha - Proyecto creado ($Formato, $($f.W)x$($f.H))."
Set-Content -Path (Join-Path $Proyecto "05_logs\edit-log.md") -Value $log -Encoding UTF8

$Fcproj = Join-Path $Proyecto "02_filmcraft\$Slug`_v01.fcproj"
if (Test-Path $Cli) {
  & $Cli --save-as $Fcproj exec file.newProject name=$Slug | Out-Null
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $Fcproj)) {
    throw "FilmCraft no pudo crear el proyecto: $Fcproj"
  }
  & $Cli --project $Fcproj --save exec file.newSequence name="Principal" width=$($f.W) height=$($f.H) fps=$($f.FPS) | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "FilmCraft no pudo crear la secuencia."
  }
} else {
  Write-Warning "No se encontro filmcraft-cli.exe. El proyecto se creo sin .fcproj."
}

Write-Host ""
Write-Host "Proyecto creado:" -ForegroundColor Green
Write-Host "  $Proyecto"
Write-Host ""
Write-Host "Brief:      $Proyecto\00_brief\brief.md"
Write-Host "FilmCraft:  $Fcproj"
Write-Host "Exportar a: $Proyecto\03_exports"
