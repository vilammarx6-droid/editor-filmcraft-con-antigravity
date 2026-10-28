# Cómo Pedir un Video al Equipo de Agentes

Esta guía te muestra cómo encargar un video al equipo de agentes con un solo mensaje y dejar que el sistema trabaje en paralelo.

---

## Opción 1: Pedido Rápido con 1 Solo Prompt (Recomendado)

Pega un mensaje similar a este en el chat de Antigravity:

```text
Director, crea un nuevo video con los siguientes datos:
- Nombre: "Danza Chumbivilcana"
- Formato: vertical_720 (TikTok / Reels)
- Duración objetivo: 45 segundos
- Estilo: Dinámico, cultural andino con toques modernos
- Fuentes: Usa la voz 'es-PE-AlexNeural', música de RECURSOS_COMPARTIDOS/01_musica
  y efectos de sonido de wakawaqra y huaylía de RECURSOS_COMPARTIDOS/02_efectos_sonido/cultural_cusco_chumbivilcas/
- Contenido: Explica qué es el toque de Wakawaqra en Santo Tomás y por qué acompaña al Takanakuy.

Ejecuta el flujo completo con tu equipo de agentes (Guionista -> Sonidista y Diseñador en paralelo -> Montajista -> Auditor QA).
```

---

## Opción 2: Flujo Paso a Paso por Fases

Si prefieres supervisar cada etapa antes de que el Montajista arme el timeline en FilmCraft:

### Fase 1: Creación del Proyecto y Brief
```powershell
.\HERRAMIENTAS\nuevo-proyecto.ps1 -Nombre "Mi Nuevo Video" -Formato vertical_720
```
Pídele al Director:
> *"Lee `PROYECTOS\AAAA-MM-DD_mi-nuevo-video\00_brief\brief.md`. Lanza al Guionista para estructurar el gancho, el guion y la tabla de escenas por segundos. No edites aún, muéstrame el plan."*

### Fase 2: Producción de Activos en Paralelo
Una vez aprobado el guion:
> *"Lanza en paralelo al Sonidista (para generar la voz WAV 48kHz con Edge-TTS y los subtítulos .srt) y al Diseñador Visual (para preparar los gráficos, viñetas y overlays)."*

### Fase 3: Contrato de Montaje y Export en FilmCraft
Crea `00_brief/edit-plan.json` con la secuencia, duración y clips. Luego ejecuta el montador determinista:
```powershell
python .\HERRAMIENTAS\montar-proyecto.py --project "PROYECTOS\AAAA-MM-DD_mi-nuevo-video"
```
El montador crea el `.fcproj`, importa y coloca los clips, verifica la timeline y exporta el master desde FilmCraft. Si necesitas inspeccionar o ajustar visualmente, abre FilmCraft con el puente:
```powershell
.\HERRAMIENTAS\abrir-filmcraft.ps1 -Proyecto "PROYECTOS\AAAA-MM-DD_mi-nuevo-video"
```
Cualquier ajuste manual debe reflejarse después en `edit-plan.json` para que el montaje siga siendo reproducible.

### Fase 4: Auditoría QA y Quality Gate
Ejecuta:
```powershell
powershell -ExecutionPolicy Bypass -File .\HERRAMIENTAS\ejecutar-pipeline.ps1 -Proyecto "PROYECTOS\AAAA-MM-DD_mi-nuevo-video"
```
El pipeline genera el collage 2x2, valida EBU R128, estéreo 48 kHz, duración y resolución, y firma `run.json` con rutas relativas y todos los artefactos.

---

## Consejos para Obtener los Mejores Resultados

1. **Especifica siempre el formato:** Indica si es `vertical_1080` (Reels/Shorts alta calidad), `vertical_720` (rápido/ligero) o `horizontal_1080` (YouTube).
2. **Aprovecha los recursos compartidos:** Menciona si quieres música lofi, memes virales (*Pedro*, *Toca Toca*, *Coffin Dance*), instrumentos andinos (*Wakawaqra*, *Pututu*) o marcos de cámara estilo `REC`.
3. **El pipeline no depende del MCP:** El montaje canónico es headless con `montar-proyecto.py`. El puente MCP (`127.0.0.1:8765`) es opcional para inspección o ajustes manuales; no sustituye el contrato `edit-plan.json`.
