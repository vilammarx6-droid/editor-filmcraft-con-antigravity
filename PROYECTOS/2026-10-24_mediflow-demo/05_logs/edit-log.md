# Bitácora de Producción — MediFlow Demo Final (`2026-10-24_mediflow-demo`)

- **2026-10-24 (v01):**
  - Creación de estructura de proyecto `horizontal_1080` (`1920x1080` @ `30 fps`, duración `300.00s` / `5:00` min).
  - **Agente 02 (Guionista):** Redacción de `00_brief/brief.md` integrando palabra por palabra las frases clave del pitch junto con el acompañamiento narrativo de cada caso clínico (Carlos, Luisa, Kevin y Portal de Pacientes).
  - **Agente 03 (Sonidista):** Síntesis de locución cálida y conversacional (`es-CO-GonzaloNeural`) en `locucion_mediflow_300s.wav` (`48000 Hz` estéreo), generación de subtítulos `.srt`, composición de pista musical indie-tech con guitarra acústica suave, ritmo de palmas acústicas y crescendo final (`musica_indie_tech_palmas_300s.wav`), y pista de efectos sincronizados (`sfx_mediflow_300s.wav`).
  - **Agente 04 (Diseñador Visual):**
    - `escena_01_flujograma_3d.mp4` (`23.00s`): Apertura cálida + Paneo de cámara 3D sobre `image.png` con pulsos luminosos animados en los 11 nodos y salida en barrido rápido (whip-pan).
    - `escena_02_urgente.mp4` (`58.40s`): `URGENTE.mp4` acelerado a `1.10x`, zooms dinámicos a la alerta crítica y pop-up animado de Slack (`#mediflow-avisos-urgentes`).
    - `escena_03_revision_humana.mp4` (`91.00s`): `REVISION_HUMANA.mp4` acelerado a `1.12x`, seguimiento de cámara al cursor en el panel derecho haciendo clic en `Resolver y registrar destino`.
    - `escena_04_rutina.mp4` (`97.16s`): `RUTINA.mp4` acelerado a `1.15x`, scroll fluido por la historia clínica de Kevin, los 11 estados verificables y el respaldo en Cloudflare R2.
    - `escena_05_portal_pacientes.mp4` (`20.44s`): `PORTAL_PACIENTES.mkv` encuadrado dinámicamente en la pantalla de un smartphone moderno.
    - `escena_06_placa_final.mp4` (`10.00s`): Placa final en movimiento con tipografía cinética mostrando `http://3.17.63.167` y `github.com/No-Country-simulation/G10-Equipo20-MediFlow` (Equipo 20).
  - **Agente 05 (Montajista):** Ensamblaje en `02_filmcraft/mediflow-demo_v01.fcproj` vía `command_batch` y exportación a `C:\Users\marx_\OneDrive\Documentos\Proyecto predeterminado\MEDIFLOW_DEMO_FINAL.mp4`.
  - **Agente 06 (Auditor QA):** Revisión de cuadrícula 2x2 (`04_previews/collage_qc.png`), ajuste de composición `alpha_composite` en nodos del flujograma 3D y refuerzo tipográfico en negrita (`Segoe UI Bold`) para máxima legibilidad en 1080p.

- **2026-10-24 (v02 — Fusión con HUD de V3 + Voz Fonética Corregida + Edición en Vivo FilmCraft `:8765`):**
  - **Voz en Off v2 (`generar_audio_mediflow_v2.py`):** Corrección fonética completa (`"Médiflou"`, `"Eslac"`, `"Cláudfler Erre Dos"`), eliminación del filtro `silenceremove` que recortaba sílabas iniciales y ajuste de velocidad a `+0%` natural (100% de las frases entraron sin aceleración forzada).
  - **Diseño Visual v2 (`generar_video_mediflow_v2.py`):**
    - Integración de las tarjetas maestras de `MEDIFLOW_DEMO_FINAL 3` con las fotografías reales de los 4 protagonistas (**Dra. Sofía**, **Dr. Alejandro**, **Dr. Mateo** y **Kevin Rojas**).
    - **Escena 01:** Tarjeta maestra con los 4 casos + paneo 3D e iluminación secuencial en los 11 nodos del flujograma + salida en barrido rápido (whip-pan).
    - **Escenas 02, 03 y 04:** Apertura con pantalla dividida (Split-Screen Acto 1, Acto 2 y Acto 3) durante los primeros 5.2s, seguida de pantalla completa con zooms dinámicos de cámara al documento y al cursor mientras la barra superior (Stepper de 4 casos) y el banner inferior (avatar circular + 4 píldoras de estado dinámicas) permanecen fijos y nítidos.
    - **Escena 05:** Tarjeta izquierda de Kevin Rojas en su sala + Smartphone moderno a la derecha mostrando `PORTAL_PACIENTES.mkv` con las pestañas de Chrome recortadas.
    - **Escena 06:** Placa final cinética con los 4 retratos circulares, la cita final, la demo activa (`http://3.17.63.167`) y el repositorio de GitHub (`github.com/No-Country-simulation/G10-Equipo20-MediFlow`).
  - **Montaje en Vivo (`mediflow-demo_v02.fcproj`):** Envío directo por `--bridge 127.0.0.1:8765` hacia la ventana abierta de FilmCraft.
