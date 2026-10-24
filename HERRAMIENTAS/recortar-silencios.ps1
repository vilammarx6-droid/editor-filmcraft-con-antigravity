param(
    [Parameter(Mandatory = $true)]
    [string]$Video,

    [Parameter(Mandatory = $false)]
    [string]$Margen = "0.2s",

    [Parameter(Mandatory = $false)]
    [string]$Salida
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Video)) {
    throw "No se encontró el video fuente: $Video"
}

$fileItem = Get-Item -LiteralPath $Video
$dir = $fileItem.DirectoryName
$baseName = $fileItem.BaseName
$ext = $fileItem.Extension

if (-not $Salida) {
    $Salida = Join-Path $dir "$($baseName)_recortado$ext"
}

Write-Host "=== Recortando silencios con Auto-Editor ===" -ForegroundColor Cyan
Write-Host "Entrada: $Video" -ForegroundColor Gray
Write-Host "Margen de habla: $Margen" -ForegroundColor Gray
Write-Host "Salida:  $Salida" -ForegroundColor Gray

& auto-editor $Video --margin $Margen -o $Salida

if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $Salida)) {
    throw "Ocurrió un error al procesar el video con auto-editor."
}

Write-Host "`n¡Video recortado exitosamente!" -ForegroundColor Green
Write-Host "Ubicación: $Salida" -ForegroundColor Green
Write-Host "El video original en 01_fuentes se mantuvo intacto." -ForegroundColor Yellow
