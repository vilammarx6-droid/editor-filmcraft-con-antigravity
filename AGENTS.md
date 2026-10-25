# Guía de Agentes y Espacio de Trabajo para FilmCraft (`EditorVideo`)

Este archivo es la instrucción principal para cualquier agente o subagente que trabaje dentro de esta carpeta.
Todo el trabajo de edición se organiza **por proyecto** y es operado por el **Equipo de 6 Agentes en Paralelo**.

---

## 1. Arquitectura del Equipo de 6 Agentes (Flujo Asíncrono)

```
                      [01. DIRECTOR ORQUESTADOR]
                                 │
                                 ▼
                        [02. EL GUIONISTA] (flash_lite)
                                 │
             ┌───────────────────┴───────────────────┐
             │ Disparo Asíncrono Simultáneo          │
             ▼                                       ▼
    [03. EL SONIDISTA] (flash_lite)       [04. EL DISEÑADOR VISUAL] (flash_lite)
  (Voz Edge-TTS, Música, SFX)            (Overlays PNG, Stickers, Croma)
             │                                       │
             └───────────────────┬───────────────────┘
                                 │ Relevo en paralelo
                                 ▼
                       [05. EL MONTAJISTA] (flash)
                 (Ensambla timeline vía FilmCraft MCP/CLI
                  en un solo `command_batch`)
                                 │
                                 ▼
                       [06. EL AUDITOR QA] (flash visión)
                 (Inspecciona collage de capturas 2x2
                  en 1 sola llamada visual)
```

### Definiciones de Subagentes en `.agents/`
1. `.agents/01_director.md` — Orquestación, validación del pedido, paralelismo y entrega final.
2. `.agents/02_guionista.md` — Estructura narrativa en `00_brief/brief.md` con gancho y tabla de tiempos (`flash_lite`).
3. `.agents/03_sonidista.md` — Locución `edge-tts` (WAV 48kHz + `.srt`), música y SFX (`flash_lite`).
4. `.agents/04_disenador_visual.md` — Selección de videos, overlays PNG, stickers y croma (`flash_lite`).
5. `.agents/05_montajista.md` — Importación y despacho masivo `command_batch` a FilmCraft (`flash`).
6. `.agents/06_auditor_qa.md` — Auditoría visual en lote sobre `04_previews/collage_qc.png` (`flash`).

---

## 2. Formatos Oficiales de Trabajo

| Clave | Uso principal | Resolución | Aspecto | FPS | Audio |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`vertical_1080`** | Reels, TikTok, Shorts (alta calidad) | `1080x1920` | `9:16` | `30` | `48000 Hz` estéreo |
| **`vertical_720`** | Reels, TikTok, Shorts (ligero / rápido) | `720x1280` | `9:16` | `30` | `48000 Hz` estéreo |
| **`horizontal_1080`** | YouTube, clases, presentaciones Full HD | `1920x1080` | `16:9` | `30` | `48000 Hz` estéreo |
| **`horizontal_720`** | Borradores rápidos o videos ligeros | `1280x720` | `16:9` | `30` | `48000 Hz` estéreo |
| **`cuadrado_1080`** | Feed cuadrado | `1080x1080` | `1:1` | `30` | `48000 Hz` estéreo |
| **`cine_1080_24`** | Estilo documental / narrativo | `1920x1080` | `16:9` | `24` | `48000 Hz` estéreo |

---

## 3. Estructura de Carpetas del Espacio

```text
EditorVideo/
├── AGENTS.md                        # Este manual maestro
├── COMO_PEDIR_UN_VIDEO.md           # Guía rápida para el usuario
├── .agents/                         # Prompts de los 6 agentes y mcp_config.json
├── HERRAMIENTAS/                    # Scripts de automatización local
│   ├── abrir-filmcraft.ps1          # Inicia FilmCraft con puente MCP (:8765)
│   ├── nuevo-proyecto.ps1           # Crea carpeta de proyecto nuevo
│   ├── generar-voz.ps1              # Crea voz neural Edge-TTS (WAV 48kHz + .srt)
│   ├── recortar-silencios.ps1       # Limpia silencios automáticamente con auto-editor
│   ├── importar-recurso.ps1         # Copia música, SFX, culturales o memes con -Filtro
│   ├── crear-collage-qa.py          # Une capturas en cuadrícula 2x2 determinista (04_previews/collage_qc.png)
│   ├── auditar-calidad.py           # Quality Gate con EBU R128 (-14 LUFS, True Peak <= -1.0 dBTP, exit 1 si falla)
│   ├── remediar-audio.py            # Normalización y remasterización a -14 LUFS / -1 dBTP
│   ├── setup-entorno.ps1            # Inicialización portable de rutas y MCP dinámico
│   └── resumir-timeline.ps1         # Resume el estado de FilmCraft sin gastar tokens
├── _PLANTILLA/                      # Plantilla base de proyecto (brief.md con sección ## Guion)
├── CREDITS.md                       # Atribuciones formales de licencias (CC-BY Kevin MacLeod, CC0)
├── RECURSOS_COMPARTIDOS/            # Biblioteca libre lista para producción (98+ activos)
│   ├── LICENSES.json                # Manifiesto estructurado de derechos y fuentes
│   ├── 01_musica/                   # Pistas libres CC-BY Incompetech + subcarpeta memes_y_virales/
│   ├── 02_efectos_sonido/           # Transiciones, impactos + cultural_cusco_chumbivilcas/ + memes_y_virales/
│   ├── 03_animaciones_y_graficos/   # Overlays, stickers_y_memes/, marcos_y_camaras/, pantalla_verde/
│   └── 04_licencias_y_fuentes/      # Fuentes TTF (Bebas Neue, Anton, Montserrat, Inter) + guía
└── PROYECTOS/                       # Un subdirectorio por cada video
```

### Estructura Interna de Cada Proyecto (`PROYECTOS/AAAA-MM-DD_slug/`)
- `00_brief/brief.md` — Objetivo, formato, guion (sección `## Guion`) y tabla de tiempos.
- `01_fuentes/` — `video/`, `audio/`, `musica/`, `graficos/` (NUNCA borrar originales).
- `02_filmcraft/` — Proyectos `.fcproj` versionados (`slug_v01.fcproj`, `slug_v02.fcproj`).
- `03_exports/` — Videos finales `.mp4` (`slug_v01_formato.mp4`).
- `04_previews/` — Capturas de revisión (`qa_01_*` a `qa_04_*`) y `collage_qc.png`.
- `05_logs/edit-log.md` — Bitácora técnica y registro de auditoría de los agentes.

---

## 4. Reglas de Oro de Rendimiento, Tokens y Seguridad

1. **Cero Charla en Subagentes:** Los subagentes tienen prohibido saludar o narrar; responden únicamente con su bloque JSON estricto.
2. **Ejecución en Paralelo:** El Sonidista (Agente 3) y el Diseñador Visual (Agente 4) se lanzan simultáneamente tras aprobarse `00_brief/brief.md`.
3. **Inspección Compacta:** Prohibido imprimir el JSON crudo de `inspect sequence` en el chat; usar siempre `HERRAMIENTAS\resumir-timeline.ps1`.
4. **Lote Único (`command_batch`):** El Montajista envía las órdenes de armado de timeline en un solo paquete usando `"params"` y los IDs numéricos de `item`.
5. **Auditoría Visual 2x2:** El Auditor QA revisa 1 sola imagen combinada (`04_previews/collage_qc.png` creada por `crear-collage-qa.py`) en lugar de abrir múltiples imágenes por separado.
6. **Seguridad No Destructiva:**
   - **Nunca borrar** archivos dentro de `01_fuentes/`.
   - **Nunca sobrescribir** un export anterior en `03_exports/` sin subir versión (`_v01`, `_v02`).
   - Guardar siempre el `.fcproj` antes de exportar.
