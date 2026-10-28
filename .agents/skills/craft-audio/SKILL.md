---
name: craft-audio
description: >-
  Procedimiento determinista para producción y procesamiento de audio en FilmCraft:
  generación de locución Edge-TTS (WAV 48kHz + SRT), remasterización y estandarización
  con SoundCraft CLI, e importación de música y SFX sin necesidad de un subagente dedicado.
---

# Craft Audio: Procedimiento de Producción Sonora (SoundCraft + Edge-TTS)

Este Skill reemplaza el overhead de invocar un subagente conversacional para tareas mecánicas de audio. Proporciona los pasos exactos y verificables para generar, procesar y estandarizar todo el audio del proyecto.

## Estándar Técnico Innegociable
- **Frecuencia de Muestreo:** `48,000 Hz` (48 kHz) estricto.
- **Canales:** 2 (Estéreo).
- **Formato de Entrega:** PCM 16/24-bit `.wav`.
- **Destino:** `01_fuentes/audio/` y `01_fuentes/musica/`.

---

## Procedimiento Paso a Paso

### 1. Generación de Locución Neural (Edge-TTS)
A partir del guion definido en `00_brief/brief.md` (sección `## Guion`), ejecutar:

```powershell
.\HERRAMIENTAS\generar-voz.ps1 -Proyecto "PROYECTOS\<slug>" -Voz "es-PE-CamilaNeural" -Tasa "+0%"
```
*Salidas verificadas:*
* `01_fuentes/audio/locucion.wav` (WAV 48 kHz estéreo)
* `01_fuentes/audio/locucion.srt` (Subtítulos temporizados)

### 2. Procesamiento y Masterización con SoundCraft CLI
Si la locución o los stems necesitan ajuste de dinámica o ecualización estándar:

```powershell
python HERRAMIENTAS\soundcraft\sc_process.py "01_fuentes\audio\locucion.wav" --rate 48000 --bit-depth 24
```
*Salida verificada:* `01_fuentes/audio/audio-manifest.json` con hash SHA-256.

### 3. Importación de Música y Efectos de Sonido (SFX)
Buscar e importar recursos de la biblioteca compartida `RECURSOS_COMPARTIDOS/`:

```powershell
# Para música de fondo:
.\HERRAMIENTAS\importar-recurso.ps1 -Proyecto "PROYECTOS\<slug>" -Tipo musica -Nombre "carefree"

# Para efectos de sonido y memes:
.\HERRAMIENTAS\importar-recurso.ps1 -Proyecto "PROYECTOS\<slug>" -Tipo sfx -Nombre "whoosh"
.\HERRAMIENTAS\importar-recurso.ps1 -Proyecto "PROYECTOS\<slug>" -Tipo memes -Nombre "vine_boom"
```

### 4. Verificación de Entrega
Antes de enviar los stems al Montajista, comprobar con PowerShell:
```powershell
Test-Path "PROYECTOS\<slug>\01_fuentes\audio\locucion.wav"
Test-Path "PROYECTOS\<slug>\01_fuentes\audio\locucion.srt"
```
Si los archivos existen físicamente, el audio está listo para ser colocado en las pistas `A1` (Locución), `A2` (Música) y `A3` (SFX) en FilmCraft.
