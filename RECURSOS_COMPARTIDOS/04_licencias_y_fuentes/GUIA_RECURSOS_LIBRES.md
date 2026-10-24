# Guía de Recursos Libres de Derechos y Herramientas para FilmCraft

Esta biblioteca central reúne medios, plantillas y herramientas para alimentar tus producciones de video en FilmCraft sin riesgo de reclamos de copyright (Content ID / Copyright Strike).

---

## 1. Contenido Descargado en este Workspace

### 🎬 RECURSOS VISUALES Y OVERLAYS (`03_animaciones_y_graficos\`)

#### 🟢 Pantallas Verdes / Chroma Key (`pantalla_verde\`):
- `explosion_pantalla_verde.mp4` — Explosión realista para memes, remates o acción.
- `boton_suscribete_pantalla_verde.mp4` — Animación de cursor dando click en "Suscribirse" y activando la campanita de notificaciones.

#### 😎 Stickers y Elementos de Meme (`stickers_y_memes\` - PNG Transparentes):
- `lentes_thug_life_meme.png` — Lentes oscuros pixelados de 8 bits para momentos épicos (*Deal with it / Turn down for what*).
- `bocadillo_dialogo_comic.png` — Globo de diálogo clásico de cómic con fondo blanco y borde negro para poner textos o diálogos cómicos.
- `bocadillo_pensamiento_cloud.png` — Nube de pensamiento para dudas o reflexiones graciosas.
- `circulo_resaltador.png` — Círculo de marcador fluorescente para encerrar detalles en pantalla.
- `flecha_amarilla.png` — Flecha gruesa amarilla con borde negro de alta visibilidad.
- `icono_check_verde.png` — Insignia redonda verde con check blanco para listas o aciertos.
- `icono_alerta_amarillo.png` — Triángulo de advertencia para notas importantes.

#### 📹 Marcos y Overlays de Cámara / Cine (`marcos_y_camaras\`):
- `overlay_camara_rec_vertical_720.png` — Visor de cámara vertical (720x1280) con corchetes, retícula (+), indicador [● REC] y batería al 98%.
- `overlay_camara_rec_horizontal_720.png` — Visor de cámara horizontal (1280x720) para formato panorámico.
- `barras_negras_cinemascope_1280x720.png` — Barras negras anamórficas (2.39:1) arriba y abajo para darle estética de película cinematográfica al video.
- `vineta_cinematica_vertical_720.png` — Viñeta suave con bordes oscurecidos para centrar la mirada en formato vertical.
- `vineta_cinematica_horizontal_720.png` — Viñeta cinematográfica para formato horizontal.

---

### 🔥 MÚSICA DE MEMES Y TRENDS VIRALES (`01_musica\memes_y_virales\`)
- `Toca_Toca_Hasta_La_Vida_Loca_Original_Meme.mp3` — El audio original de TikTok: *"Hasta la vida loca, loca, loca, loca... Te encanta la música, te toca, toca, toca"*.
- `Pedro_Pedro_Pedro_Meme_Mapache.mp3` — El hit viral del mapache (*Pedro Pedro Pedro Pe*).
- `Astronomia_Coffin_Dance_Meme.mp3` — El baile del ataúd de Ghana.
- `GigaChad_Can_You_Feel_My_Heart.mp3` — El tema de Chad / Sigma.
- `To_Be_Continued_Roundabout_Meme.mp3` — El tema de *"To Be Continued..."* antes de un desastre.
- `Run_Awolnation_Meme.mp3` — El grito *"RUN!"* para persecuciones y sustos.
- `Careless_Whisper_Saxophone_Meme.mp3` — Solo de saxofón seductor y cómico.
- `Monkeys_Spinning_Monkeys.mp3` — El fondo alegre de flauta #1 de TikTok.
- `Sneaky_Snitch.mp3` — Cuerdas sigilosas para travesuras.
- `Fluffing_a_Duck.mp3`, `Scheming_Weasel.mp3`, `Elevator_Music_Meme.mp3`.

---

### 🇵🇪 CULTURAL CUSCO Y CHUMBIVILCAS (`02_efectos_sonido\cultural_cusco_chumbivilcas\`)
- `wakawaqra_toque_tradicional_completo.wav`, `wakawaqra_llamada_corta.wav`, `wakawaqra_diana_corrida.wav`, `wakawaqra_remate_takanakuy.wav`, `wakawaqra_eco_andino_montana.wav`.
- `chillador_rasgueo_huaylia_chumbivilcana.wav`, `pututu_llamada_ceremonial_inca.wav`, `tinya_bombo_andino_tradicional.wav`, `cascabeles_espuelas_qorilazo.wav`, `fiesta_comparsa_carnavalesca.wav`, `voz_quechua_chumbivilcas.wav`.

---

### 🔤 FUENTES PARA TÍTULOS (`04_licencias_y_fuentes\fuentes\`)
- `BebasNeue-Regular.ttf`, `Anton-Regular.ttf`, `Montserrat-Variable.ttf`, `Inter-Variable.ttf`.

---

## 2. Herramientas Automatizadas del Editor

```powershell
# Importa TODO al proyecto activo:
.\HERRAMIENTAS\importar-recurso.ps1 -Proyecto "PROYECTOS\AAAA-MM-DD_slug"

# Importa solo recursos VISUALES (imágenes a graficos y pantallas verdes a video):
.\HERRAMIENTAS\importar-recurso.ps1 -Proyecto "PROYECTOS\AAAA-MM-DD_slug" -Tipo graficos

# Importa solo MEMES (música y SFX virales):
.\HERRAMIENTAS\importar-recurso.ps1 -Proyecto "PROYECTOS\AAAA-MM-DD_slug" -Tipo memes

# Importa solo recursos CULTURALES:
.\HERRAMIENTAS\importar-recurso.ps1 -Proyecto "PROYECTOS\AAAA-MM-DD_slug" -Tipo cultural
```
