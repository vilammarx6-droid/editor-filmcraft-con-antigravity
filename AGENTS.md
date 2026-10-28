# Guía de Agentes y Espacio de Trabajo para FilmCraft (`EditorVideo`)

Este archivo es la instrucción principal para cualquier agente, subagente o script que trabaje dentro de este repositorio.
Todo el trabajo de edición se organiza **por proyecto** y es operado mediante la **Arquitectura Híbrida Verificable**: orquestación cognitiva en Antigravity con subagentes especializados, contratos JSON estrictos y los 4 motores deterministas de la suite Craft: **FilmCraft CLI** (NLE), **EffectCraft CLI** (Motion Graphics), **PhotoCraft CLI** (Miniaturas) y **SoundCraft CLI** (Audio y Mastering).

---

## 1. Arquitectura Híbrida Verificable (Agentes Cognitivos + Skills Deterministas)

Para evitar alucinaciones, reportes prematuros y pérdidas de tiempo, el sistema separa las decisiones creativas y espaciales de la ejecución mecánica mediante **Skills On-Demand** y **Agentes Cognitivos Especializados** (adoptando principios de `agency-agents`):

```text
                      [01. DIRECTOR ORQUESTADOR] (Antigravity)
                                  │
                                  ▼
                    [02. EL GUIONISTA / STORYTELLER] (flash_lite)
             (Escribe 00_brief/brief.md con gancho visual y tabla de beats)
                                  │
              ┌───────────────────┴───────────────────┐
              │ Contratos y Pautas en Paralelo        │
              ▼                                       ▼
     [SKILL: CRAFT-AUDIO]                   [04. DISEÑADOR VISUAL / REMOTION]
     (SoundCraft CLI + Edge-TTS)            (EffectCraft + Remotion 4.x CLI)
     (WAV 48kHz + SRT sin subagente)        (ProRes 4444 RGBA + Subtítulos Cinéticos)
              │                                       │
              └───────────────────┬───────────────────┘
                                  │ Ingesta y Montaje
                                  ▼
                        [05. EL MONTAJISTA] (flash / CLI)
                  (Lee 00_brief/edit-plan.json y ejecuta montar-proyecto.py:
                   importa, corta y coloca clips en V1..V3 / A1..A3,
                   verifica la timeline y exporta el master desde FilmCraft)
                                  │
                                  ▼
                       [SKILL: CRAFT-THUMBNAILS]
                  (PhotoCraft CLI 0.16.0 thumbnail.jpg + manifest)
                                  │
                                  ▼
                      [SKILL: CRAFT-QUALITY-GATE]
                  - Sonoridad EBU R128: [-16, -13] LUFS (Hard Fail)
                  - True Peak: <= -1.0 dBTP (Hard Fail si supera)
                  - Collage visual 2x2 determinista (Safe Zones)
                                  │
              ┌───────────────────┴───────────────────┐
              │ ¿El usuario pide ajustes puntuales?   │
              ▼                                       ▼
     [06. CIRUJANO DE REVISIONES]           [LIBRO MAYOR CRIPTOGRÁFICO]
     (Minimal Change Engineer)              (Registra SHA-256 en run.json)
     (Zero scope creep, parches a .fcproj)
```

### Definiciones en `.agents/`

#### A. Agentes Cognitivos Especializados
1. `.agents/01_director.md` — Orquestación, supervisión de ciclo de vida, despacho de agentes y ejecución de skills.
2. `.agents/02_guionista.md` — Narrativa audiovisual, hooks en los primeros 3 segundos y tabla de beats (*Visual Storyteller* y *TikTok Strategist*).
3. `.agents/04_disenador_visual.md` — Identidad visual, tipografía Bebas/Anton, márgenes seguros y contrato `diseno.json` ProRes RGBA (*Brand Guardian*).
4. `.agents/05_montajista.md` — Montaje determinista desde `00_brief/edit-plan.json` con `HERRAMIENTAS/montar-proyecto.py`: importa fuentes, coloca clips en pistas multitrack, verifica la timeline y exporta el master desde FilmCraft.
5. `.agents/06_cirujano_revisiones.md` — Modificaciones quirúrgicas no destructivas sobre proyectos existentes (*Minimal Change Engineer*, cero *scope creep*).

#### B. Skills Deterministas de Ejecución Rápida (`.agents/skills/`)
1. `craft-audio` — Generación de locución neural Edge-TTS (WAV 48kHz + SRT), procesamiento de stems con SoundCraft CLI e importación de SFX/música.
2. `craft-remotion` — Generación de subtítulos cinéticos palabra por palabra, infografías animadas y rótulos web con Remotion 4.x CLI (`rem_render.py`) en ProRes 4444 RGBA con canal alfa.
3. `craft-thumbnails` — Renderizado determinista de miniaturas y portadas de alto CTR con PhotoCraft CLI y manifiesto SHA-256.
4. `craft-quality-gate` — Calificación estricta EBU R128 (`auditar-calidad.py`), collage 2x2 (`crear-collage-qa.py`) y verificación de márgenes seguros.

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
├── CREDITS.md                       # Atribuciones formales de licencias (CC-BY Kevin MacLeod, CC0)
├── .agents/                         # Prompts de agentes, plantillas y mcp_config.json
├── HERRAMIENTAS/                    # Scripts de automatización local y Quality Gate
│   ├── setup-entorno.ps1            # Descubrimiento dinámico de rutas y generador MCP
│   ├── test-pipeline-suite.ps1      # Suite de 9 pruebas herméticas (edición real + negativas)
│   ├── ejecutar-pipeline.ps1        # Orquestador: edit-plan -> montaje -> export -> Quality Gate
│   ├── montar-proyecto.py           # Montador determinista: edit-plan.json -> .fcproj + master
│   ├── auditar-calidad.py           # Quality Gate EBU R128 + canales + duración
│   ├── remediar-audio.py            # Normalización y remasterización a -14 LUFS / -1 dBTP
│   ├── effectcraft/                 # Motor de Motion Graphics (EffectCraft CLI 0.11.1)
│   │   ├── ec_render.py             # Renderizador ProRes 4444 RGBA y emisor de manifiesto
│   │   ├── validar-render.ps1       # Suite de validación con 3 pruebas negativas
│   │   └── templates/               # Plantillas limpias compiladas (.ectemplate)
│   ├── remotion/                    # Motor de Gráficos Web y Subtítulos Dinámicos (Remotion 4.x)
│   │   ├── rem_render.py            # Renderizador ProRes 4444 RGBA / MP4 y emisor de manifiesto
│   │   ├── package.json             # Dependencias React + Remotion CLI
│   │   └── src/                     # Composiciones React (Subtítulos cinéticos, infografías, rótulos)
│   ├── abrir-filmcraft.ps1          # Inicia FilmCraft con puerto MCP (:8765) de forma segura
│   ├── nuevo-proyecto.ps1           # Crea estructura con plantilla y sección ## Guion
│   ├── generar-voz.ps1              # Crea voz neural Edge-TTS (WAV 48kHz + .srt)
│   ├── recortar-silencios.ps1       # Limpia silencios automáticamente con auto-editor
│   ├── importar-recurso.ps1         # Copia activos con filtro por nombre
│   ├── crear-collage-qa.py          # Une capturas en cuadrícula 2x2 determinista
│   └── resumir-timeline.ps1         # Resumen compacto de FilmCraft en disco o memoria
├── _PLANTILLA/                      # Plantilla base de proyecto (brief.md con sección ## Guion)
├── RECURSOS_COMPARTIDOS/            # Biblioteca libre lista para producción (98+ activos)
│   ├── LICENSES.json                # Manifiesto estructurado de derechos y fuentes
│   ├── 01_musica/                   # Pistas libres CC-BY Incompetech + memes_y_virales/
│   ├── 02_efectos_sonido/           # SFX de cine + cultural_cusco_chumbivilcas/ + memes_y_virales/
│   ├── 03_animaciones_y_graficos/   # Overlays, viñetas, marcos_y_camaras/, pantalla_verde/
│   └── 04_licencias_y_fuentes/      # Fuentes TTF (Bebas Neue, Anton, Montserrat, Inter)
└── PROYECTOS/                       # Un subdirectorio por cada video
    └── test-golden-10s/             # Proyecto Golden de prueba integral verificado
```

### Estructura Interna de Cada Proyecto (`PROYECTOS/AAAA-MM-DD_slug/`)
- `00_brief/brief.md` — Objetivo, formato, guion (sección obligatoria `## Guion`) y tabla de tiempos.
- `00_brief/edit-plan.json` — **Contrato de montaje obligatorio**: secuencia, duración, pistas y clips con `start`/`in`/`out`.
- `01_fuentes/` — `video/`, `audio/`, `musica/`, `graficos/` (NUNCA borrar originales).
- `02_filmcraft/` — Proyectos `.fcproj` reales y versionados (`slug_v01.fcproj`) + `edit-manifest.json`.
- `03_exports/` — Videos finales `.mp4` validados por el Quality Gate (`_timeline.mp4` y `_master.mp4`).
- `04_previews/` — Capturas de revisión (`qa_01_*` a `qa_04_*`) y `collage_qc.png`.
- `05_logs/` — Bitácora `edit-log.md` y registro criptográfico `run.json`.

---

## 4. Montaje Determinista desde `edit-plan.json`

El pipeline **ya no valida un timeline existente como si fuera una edición nueva**. El contrato de montaje es `00_brief/edit-plan.json` y el único ejecutor es `HERRAMIENTAS/montar-proyecto.py`.

```json
{
  "schema_version": "1.0.0",
  "project": "2026-10-26_mi-proyecto",
  "sequence": { "name": "Principal", "width": 720, "height": 1280, "fps": 30, "sample_rate": 48000, "video_tracks": 3, "audio_tracks": 2 },
  "duration": 30.0,
  "allow_gaps": false,
  "tracks": {
    "V1": [
      { "source": "video/escena_01.mp4", "start": 0.0, "in": 0.0, "out": 10.0 },
      { "source": "video/escena_02.mp4", "start": 10.0, "in": 0.0, "out": 20.0 }
    ],
    "V2": [
      { "source": "graficos/overlay_01.mov", "start": 1.0, "in": 0.0, "out": 3.0 }
    ],
    "A1": [
      { "source": "audio/locucion_master.wav", "start": 0.0, "in": 0.0, "out": 30.0 }
    ],
    "A2": [
      { "source": "musica/musica_48k.wav", "start": 0.0, "in": 0.0, "out": 30.0 }
    ]
  },
  "output": { "slug": "mi-proyecto" }
}
```

- Las rutas son **relativas a `01_fuentes/`**. Para la biblioteca compartida se usa `"source_root": "shared"` y una `"license"` obligatoria.
- `montar-proyecto.py` valida existencia, duración real, solapamientos, huecos de V1, nombres duplicados y pistas; crea el `.fcproj`, importa los medios, coloca los clips, verifica la timeline contra el plan, exporta desde FilmCraft, normaliza el audio y ejecuta el Quality Gate antes de firmar el manifiesto.
- Salidas versionadas: `02_filmcraft/<slug>_vNN.fcproj`, `03_exports/<slug>_vNN_timeline.mp4`, `03_exports/<slug>_vNN_master.mp4` y `02_filmcraft/edit-manifest_vNN.json` + `edit-manifest.json`.
- El manifiesto incluye SHA-256 del plan, timeline, master y materias primas. El `run.json` debe usar rutas relativas y registrar todos los clips/música/plan/manifiesto.
- El esquema de referencia está en `HERRAMIENTAS/esquema-edit-plan.schema.json`.

### Comandos

```powershell
# Montaje + export + normalización + Quality Gate interno
python .\HERRAMIENTAS\montar-proyecto.py --project "PROYECTOS\mi-proyecto"

# Solo montar y verificar la timeline (sin exportar)
python .\HERRAMIENTAS\montar-proyecto.py --project "PROYECTOS\mi-proyecto" --no-export

# Pipeline completo: exige edit-plan.json
powershell -ExecutionPolicy Bypass -File .\HERRAMIENTAS\ejecutar-pipeline.ps1 -Proyecto "PROYECTOS\mi-proyecto"

# Auditoría explícita de un proyecto ya montado, sin editar nada
powershell -ExecutionPolicy Bypass -File .\HERRAMIENTAS\ejecutar-pipeline.ps1 -Proyecto "PROYECTOS\mi-proyecto" -PermitirTimelineExistente
```

`-PermitirTimelineExistente` es **solo para auditar** un proyecto histórico; no autoriza a copiar un `.fcproj` ajeno.

---

## 5. Reglas de Oro de Rendimiento, Tokens y Calidad

1. **Cero Reportes Anticipados (Regla Anti-Alucinación):** Ningún agente puede reportar `"status": "ok"` o `"completado"` sin que el archivo físico exista en disco y su hash sea verificable.
2. **Contratos Formales de Diseño:** El Diseñador no genera renders ciegos; produce `diseno.json` validado contra `essential.templateInfo`. El motor `ec_render.py` produce el render y el `render-manifest.json` con SHA-256.
3. **Quality Gate Innegociable:** El audio DEBE cumplir EBU R128 con sonoridad integrada en `[-16.0, -13.0] LUFS` y True Peak $\le -1.0$ dBTP. Si supera estos umbrales, el pipeline falla con `exit 1`. También se valida que el audio sea estéreo 48 kHz y que la duración coincida con el plan.
4. **Líneas de Tiempo Multitrack Reales:** Todo export debe originarse en un `.fcproj` creado por `montar-proyecto.py` desde `edit-plan.json`, guardado en disco y con pistas organizadas (`V1`, `V2`, `A1`, `A2`). No se aceptan timelines copiados de otro proyecto.
5. **Inspección Compacta:** Prohibido imprimir el JSON crudo de `inspect sequence` en el chat; usar siempre `HERRAMIENTAS\resumir-timeline.ps1 -ForzarDisco`.
6. **Seguridad No Destructiva:**
   - **Nunca borrar** archivos dentro de `01_fuentes/`.
   - **Nunca sobrescribir** un export anterior en `03_exports/` sin subir versión (`_v01`, `_v02`).
   - Guardar siempre el `.fcproj` antes de exportar.
   - `run.json` no debe contener rutas absolutas ni artefactos Auto-Save.
