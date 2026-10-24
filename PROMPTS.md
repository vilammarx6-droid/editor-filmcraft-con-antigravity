# Prompts

## Antes de empezar
FilmCraft debe estar abierto con el proyecto. Si no, ejecuta:

```powershell
.\HERRAMIENTAS\abrir-filmcraft.ps1 -Proyecto "PROYECTOS\AAAA-MM-DD_slug"
```

Deja la ventana de FilmCraft abierta mientras Antigravity edita.

## Generación de Locución (Opcional)
Genera la locución y los subtítulos para el proyecto actual basándote en el guion de `00_brief/brief.md` usando la voz [es-PE-AlexNeural / es-MX-DaliaNeural / es-ES-AlvaroNeural]. Guarda los archivos en `01_fuentes/audio`.

## Recorte de Silencios (Opcional)
Analiza el video crudo en `01_fuentes/video/[nombre_video.mp4]` y recorta los silencios y pausas largas con auto-editor. Usa la versión recortada para la edición.

## Importar Música y Efectos Compartidos
Importa música de fondo y efectos de sonido desde la carpeta `RECURSOS_COMPARTIDOS` a este proyecto usando `importar-recurso.ps1`.

## Auditoría y plan
Lee `00_brief/brief.md`. Fase 1: auditoría y plan. No edites nada. Inspecciona las fuentes, propón estructura de escenas con tiempos, textos en pantalla y música. Espera mi aprobación.

## Edición
Ejecuta el plan aprobado. Crea el proyecto en `02_filmcraft`, importa solo los medios del brief y monta la secuencia. Guarda con `file.save`. Genera 3 previews en `04_previews` con `max_side=480`. No exportes todavía.

## Ajustes
Revisa los previews y aplica estos cambios: [CAMBIOS]. Guarda una nueva versión `_v02`. Genera 3 previews nuevos.

## Exportación
Exporta la secuencia activa a `03_exports` con el formato del brief, H.264, audio AAC 48 kHz. Nombre: `slug_v01_formato.mp4`. No sobrescribas exports anteriores.
