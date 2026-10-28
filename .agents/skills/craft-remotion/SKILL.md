---
name: craft-remotion
description: >-
  Procedimiento determinista para generacion de subtitulos cineticos animados estilo redes,
  infografias de datos dinamicas y rotulos modernos usando Remotion CLI (rem_render.py).
  Exporta en Apple ProRes 4444 RGBA con canal alfa real e integra manifiesto criptografico
  SHA-256 compatible con FilmCraft y el Quality Gate.
---

# Craft Remotion: Motor de Gráficos y Subtítulos Dinámicos (Remotion)

Este Skill dota a los agentes de Antigravity de la capacidad de programar, renderizar y auditar gráficos dinámicos, infografías de datos y subtítulos cinéticos (palabra por palabra) usando **Remotion (React + TypeScript)**.

## Cuándo Usar Remotion frente a EffectCraft
* **Usar Remotion:**
  * Subtítulos palabra por palabra animados (estilo TikTok / Reels / Shorts) a partir de archivos `.srt` o transcripciones Whisper.
  * Infografías de datos, dashboards, barras de progreso o contadores crecientes.
  * Diseños basados en CSS/React con tipografías web y sombras volumétricas.
* **Usar EffectCraft:**
  * Rótulos clásicos basados en plantillas `.ectemplate` preestablecidas.

---

## Composiciones Nativas Disponibles (`HERRAMIENTAS/remotion/src/Root.tsx`)

| Composición | Resolución | Formato | Propósito |
| :--- | :---: | :---: | :--- |
| `SubtitulosKineticVertical` | 720x1280 | 9:16 (30fps) | Subtítulos animados palabra por palabra para Shorts/TikTok. |
| `SubtitulosKineticHorizontal` | 1280x720 | 16:9 (30fps) | Subtítulos dinámicos de alto contraste para YouTube horizontal. |
| `InfografiaVertical` | 720x1280 | 9:16 (30fps) | Tarjeta flotante con porcentaje, badge, título y barra animada. |
| `InfografiaHorizontal` | 1280x720 | 16:9 (30fps) | Tarjeta lateral con estadísticas y métricas clave. |
| `LowerThirdModern` | 1280x720 | 16:9 (30fps) | Rótulo inferior con badge temático y estilo cristal oscuro. |

---

## Procedimiento de Renderizado y Validación

### 1. Renderizado de Subtítulos Cinéticos desde Archivo SRT
Para tomar la locución generada (`locucion.srt`) y crear un overlay transparente sincronizado:

```powershell
python HERRAMIENTAS\remotion\rem_render.py `
  --comp "SubtitulosKineticVertical" `
  --srt "PROYECTOS\<slug>\01_fuentes\audio\locucion.srt" `
  --format "prores" `
  --channels "rgba" `
  --output "PROYECTOS\<slug>\01_fuentes\graficos\overlay_subtitulos.mov"
```

### 2. Renderizado de Infografía de Datos Dinámicos
Para ilustrar estadísticas o cifras del guion:

```powershell
python HERRAMIENTAS\remotion\rem_render.py `
  --comp "InfografiaHorizontal" `
  --props '{"badge":"TELEMEDICINA","titulo":"COBERTURA RURAL","valorPrincipal":"92%","subtitulo":"Comunidades conectadas","porcentajeBarra":92,"colorAcento":"#38BDF8"}' `
  --format "prores" `
  --channels "rgba" `
  --output "PROYECTOS\<slug>\01_fuentes\graficos\overlay_infografia.mov"
```

### 3. Montaje en FilmCraft Multitrack
El archivo `.mov` generado en ProRes 4444 con transparencia real (`yuva444p12le`) se monta sobre la pista superior de video:
* **Video 1:** Clips de cámara o metraje base (B-roll).
* **Video 2:** Overlays de rótulos o infografías.
* **Video 3:** Overlays de subtítulos cinéticos.

### 4. Verificación Criptográfica en el Quality Gate
`rem_render.py` emite automáticamente en la carpeta de destino:
* `render-manifest.json`
* `render-manifest-<comp>.json`

El orquestador `ejecutar-pipeline.ps1` detecta los manifiestos, valida que `has_alpha == true` y comprueba que el hash SHA-256 coincida exactamente con el archivo en disco antes de firmar `run.json`.

---

## Previsualización en Vivo (Remotion Studio)
Para depurar y ajustar animaciones en tiempo real en el navegador:
```powershell
cd HERRAMIENTAS\remotion
npm start
# Abre automáticamente http://localhost:3000 con timeline interactivo
```
