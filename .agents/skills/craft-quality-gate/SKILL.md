---
name: craft-quality-gate
description: >-
  Quality Gate determinista para exportaciones de video y audio en FilmCraft.
  Auditoría de sonoridad EBU R128 (-16 a -13 LUFS, True Peak <= -1.0 dBTP),
  inspección visual de collage 2x2, validación de márgenes seguros de plataforma
  (estilo ui-finish-gate-reviewer) y verificación criptográfica de manifiestos.
---

# Craft Quality Gate: Auditoría y Aprobación Final de Master

Inspirado en el estándar de revisión `ui-finish-gate-reviewer` y el Quality Gate acústico EBU R128. Este Skill proporciona los criterios objetivos y scripts de comprobación para certificar que un video está listo para entrega.

---

## Criterios del Quality Gate (Pase / Fallo Innegociable)

| Parámetro | Rango Aceptable | Herramienta | Tipo de Fallo |
| :--- | :--- | :--- | :--- |
| **Sonoridad Integrada (EBU R128)** | `[-16.0, -13.0] LUFS` | `auditar-calidad.py` | **Hard Fail** (exit 1) |
| **True Peak Máximo** | `≤ -1.0 dBTP` | `auditar-calidad.py` | **Hard Fail** (exit 1) |
| **Frecuencia de Audio** | `48,000 Hz` estéreo | FFprobe / SoundCraft | **Hard Fail** |
| **Gráficos y Manifiestos** | `has_alpha: true` y hash verificado | `render-manifest.json` | **Hard Fail** |
| **Márgenes Seguros UI** | 15% lateral, 20% inferior libre | Inspección de `collage_qc.png` | **Soft Warning / Ajuste** |

---

## Procedimiento de Auditoría

### 1. Auditoría de Audio EBU R128
Ejecutar el script evaluador sobre el export final:
```powershell
python HERRAMIENTAS\auditar-calidad.py "PROYECTOS\<slug>\03_exports\<master>.mp4"
```
* **Si sale con éxito (0):** El audio cumple con las normas de transmisión para plataformas digitales.
* **Si falla (exit 1):** Ejecutar la remediación automática:
  ```powershell
  python HERRAMIENTAS\remediar-audio.py "PROYECTOS\<slug>\03_exports\<master>.mp4"
  ```

### 2. Generación y Revisión de Collage 2x2
Generar la cuadrícula visual de control:
```powershell
python HERRAMIENTAS\crear-collage-qa.py "PROYECTOS\<slug>"
```
*Comprobaciones visuales obligatorias en `04_previews/collage_qc.png`:*
1. **Legibilidad y Contraste:** El texto (títulos y subtítulos) tiene suficiente contraste contra el fondo (uso de sombras, trazos o viñetas).
2. **Safe Zones (Zona Segura):** En videos verticales (`vertical_1080` / `vertical_720`), los subtítulos no deben estar pegados al borde inferior (zona tapada por el reproductor de TikTok/Reels) ni en el borde lateral derecho (zona de botones de like/comentar).
3. **Fotogramas Negros:** Verificar que no existan huecos de clips o transiciones mal calculadas en `V1`.

### 3. Registro en el Ledger Criptográfico (`run.json`)
Una vez aprobado el Quality Gate, registrar el SHA-256 inmutable del master final en `05_logs/run.json`.
