# Guía de Agentes y Espacio de Trabajo para FilmCraft (`EditorVideo`)

Este archivo es la instrucción principal para cualquier agente, subagente o script que trabaje dentro de este repositorio.
Todo el trabajo de edición se organiza **por proyecto** y es operado mediante la **Arquitectura Híbrida Verificable**: orquestación cognitiva en Antigravity con subagentes especializados, contratos JSON estrictos y los 4 motores deterministas de la suite Craft: **FilmCraft CLI** (NLE), **EffectCraft CLI** (Motion Graphics), **PhotoCraft CLI** (Miniaturas) y **SoundCraft CLI** (Audio y Mastering).

---

## 1. Arquitectura Híbrida Verificable (3 Capas)

Para evitar alucinaciones, reportes prematuros y pérdidas de tiempo, el sistema separa estrictamente la toma de decisiones cognitivas de la ejecución técnica verificable:

```text
                      [01. DIRECTOR ORQUESTADOR] (Antigravity)
                                  │
                                  ▼
                         [02. EL GUIONISTA] (flash_lite)
                         (Escribe 00_brief/brief.md con ## Guion)
                                  │
              ┌───────────────────┼───────────────────┐
              │ Contratos y Pautas en Paralelo        │
              ▼                   ▼                   ▼
     [03. EL SONIDISTA]  [04. DISEÑADOR VISUAL] [07. DISEÑADOR MINIATURAS]
      (SoundCraft CLI +   (EffectCraft CLI       (PhotoCraft CLI 0.16.0
       Edge-TTS + FFmpeg)  ProRes 4444 RGBA)      thumbnail.jpg + manifest)
              │                   │                   │
              └───────────────────┴─────────┬─────────┘
                                            │ Ingesta, Miniatura y Montaje
                                            ▼
                                  [05. EL MONTAJISTA] (flash / CLI)
                            (Monta timeline nativo en FilmCraft CLI / MCP
                             en pistas V1, V2, V3, A1, A2, A3; guarda .fcproj)
                                            │
                                            ▼
                                  [06. EL AUDITOR QA] (flash visión)
                            (Inspecciona collage 2x2 determinista)
                                            │
                                            ▼
                            [QUALITY GATE ESTRICTO (auditar-calidad.py)]
                            - Sonoridad EBU R128: [-16, -13] LUFS (Hard Fail)
                            - True Peak: <= -1.0 dBTP (Hard Fail si supera)
                            - Duración y sample rate: 48000 Hz estéreo
                                            │
                                            ▼
                              [LIBRO MAYOR CRIPTOGRÁFICO (run.json)]
                            (Registra SHA-256 inmutable de los artefactos)
```

### Definiciones de Subagentes en `.agents/`
1. `.agents/01_director.md` — Orquestación, validación del pedido, gestión de dependencias y auditoría del ledger `run.json`.
2. `.agents/02_guionista.md` — Estructura narrativa en `00_brief/brief.md` con gancho y tabla de tiempos (`flash_lite`).
3. `.agents/03_sonidista.md` — Locución `edge-tts` (WAV 48kHz + `.srt`), procesamiento de stems en **SoundCraft CLI** y SFX (`flash_lite`).
4. `.agents/04_disenador_visual.md` — Contrato `diseno.json` para **EffectCraft CLI 0.11.1** con ProRes RGBA y canal alfa (`flash_lite`).
5. `.agents/05_montajista.md` — Importación y despacho de clips al timeline de **FilmCraft CLI** (`flash` o headless CLI).
6. `.agents/06_auditor_qa.md` — Auditoría visual sobre `04_previews/collage_qc.png` (`flash`).
7. `.agents/07_disenador_miniaturas.md` — Generación de portadas y miniaturas con **PhotoCraft CLI 0.16.0** (`flash_lite`).

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
│   ├── test-pipeline-suite.ps1      # Suite de 5 pruebas de integridad (Happy + 4 Negativas)
│   ├── ejecutar-pipeline.ps1        # Pipeline unificado con Quality Gate y run.json
│   ├── auditar-calidad.py           # Quality Gate EBU R128 con Hard Fail (exit 1)
│   ├── remediar-audio.py            # Normalización y remasterización a -14 LUFS / -1 dBTP
│   ├── effectcraft/                 # Motor de Motion Graphics (EffectCraft CLI 0.11.1)
│   │   ├── ec_render.py             # Renderizador ProRes 4444 RGBA y emisor de manifiesto
│   │   ├── validar-render.ps1       # Suite de validación con 3 pruebas negativas
│   │   └── templates/               # Plantillas limpias compiladas (.ectemplate)
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
- `01_fuentes/` — `video/`, `audio/`, `musica/`, `graficos/` (NUNCA borrar originales).
- `02_filmcraft/` — Proyectos `.fcproj` reales y versionados (`slug_v01.fcproj`).
- `03_exports/` — Videos finales `.mp4` validados por el Quality Gate.
- `04_previews/` — Capturas de revisión (`qa_01_*` a `qa_04_*`) y `collage_qc.png`.
- `05_logs/` — Bitácora `edit-log.md` y registro criptográfico `run.json`.

---

## 4. Reglas de Oro de Rendimiento, Tokens y Calidad

1. **Cero Reportes Anticipados (Regla Anti-Alucinación):** Ningún agente puede reportar `"status": "ok"` o `"completado"` sin que el archivo físico exista en disco y su hash sea verificable.
2. **Contratos Formales de Diseño:** El Diseñador no genera renders ciegos; produce `diseno.json` validado contra `essential.templateInfo`. El motor `ec_render.py` produce el render y el `render-manifest.json` con SHA-256.
3. **Quality Gate Innegociable:** El audio DEBE cumplir EBU R128 con sonoridad integrada en `[-16.0, -13.0] LUFS` y True Peak $\le -1.0$ dBTP. Si supera estos umbrales, el pipeline falla con `exit 1`.
4. **Líneas de Tiempo Multitrack Reales:** Todo export debe originarse en un proyecto nativo `.fcproj` guardado en disco con pistas organizadas (`V1`, `V2`, `A1`, `A2`).
5. **Inspección Compacta:** Prohibido imprimir el JSON crudo de `inspect sequence` en el chat; usar siempre `HERRAMIENTAS\resumir-timeline.ps1`.
6. **Seguridad No Destructiva:**
   - **Nunca borrar** archivos dentro de `01_fuentes/`.
   - **Nunca sobrescribir** un export anterior en `03_exports/` sin subir versión (`_v01`, `_v02`).
   - Guardar siempre el `.fcproj` antes de exportar.
