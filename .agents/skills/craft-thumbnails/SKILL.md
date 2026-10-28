---
name: craft-thumbnails
description: >-
  Procedimiento determinista para generación de miniaturas y portadas de alto CTR
  usando PhotoCraft CLI (pc_thumbnail.py). Selecciona el mejor keyframe, aplica tipografía
  de impacto de RECURSOS_COMPARTIDOS y emite el manifiesto verificado sin overhead de subagente.
---

# Craft Thumbnails: Procedimiento de Portadas y Miniaturas (PhotoCraft)

Este Skill reemplaza el overhead de invocar un subagente dedicado para la creación de miniaturas estáticas. Define el flujo exacto y los estándares de composición para portadas de alto CTR (*Click-Through Rate*).

## Estándar Técnico y Formatos
- **Resolución YouTube / Horizontal:** `1920x1080` (16:9).
- **Resolución TikTok / Reels / Shorts:** `1080x1920` (9:16).
- **Resolución Feed / Cuadrado:** `1080x1080` (1:1).
- **Fuentes Aprobadas (`RECURSOS_COMPARTIDOS/04_licencias_y_fuentes/`):**
  - Titulares principales: *Anton-Regular.ttf* o *BebasNeue-Regular.ttf* (impacto alto y legibilidad).
  - Subtítulos o texto secundario: *Montserrat-Bold.ttf* o *Inter-Bold.ttf*.
- **Salida:** `03_exports/thumbnail.jpg` + `03_exports/thumbnail-manifest.json`.

---

## Procedimiento Paso a Paso

### 1. Identificar el Keyframe de Base
Seleccionar el fotograma más expresivo o representativo generado durante la fase de montaje:
* Preferencia 1: `04_previews/qa_01_frame.png`
* Preferencia 2: `04_previews/collage_qc.png`
* Preferencia 3: Extraer fotograma específico del video master con FFmpeg:
  ```powershell
  ffmpeg -ss 00:00:03 -i "PROYECTOS\<slug>\03_exports\<master>.mp4" -vframes 1 -q:v 2 "PROYECTOS\<slug>\04_previews\frame_key.png" -y
  ```

### 2. Ejecutar el Motor PhotoCraft CLI
Llamar al motor de composición estática pasando el título de gancho y el aspecto:

```powershell
python HERRAMIENTAS\photocraft\pc_thumbnail.py `
  --project "PROYECTOS\<slug>" `
  --title "TITULO CORTO DE ALTO IMPACTO" `
  --aspect "16:9"
```

### 3. Verificación de Entrega Criptográfica
Comprobar que existan en disco el archivo de imagen y su contrato:
```powershell
Test-Path "PROYECTOS\<slug>\03_exports\thumbnail.jpg"
Test-Path "PROYECTOS\<slug>\03_exports\thumbnail-manifest.json"
```
El manifiesto `thumbnail-manifest.json` debe contener `"status": "ok"` y el hash SHA-256 verificado.
