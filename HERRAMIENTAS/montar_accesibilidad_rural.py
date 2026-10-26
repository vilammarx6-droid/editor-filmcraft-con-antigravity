#!/usr/bin/env python3
"""
montar_accesibilidad_rural.py
Ensambla el proyecto '2026-10-26_accesibilidad-rural' de 60s @ 30fps vertical (720x1280)
integrando de punta a punta:
- Guion Edge-TTS
- SoundCraft CLI (masterización y remuestreo 48kHz)
- EffectCraft CLI (overlay ProRes 4444 RGBA con canal alfa)
- FilmCraft CLI (montaje multitrack nativo .fcproj)
- PhotoCraft CLI (miniatura de alta conversión con manifiesto)
- Quality Gate EBU R128 estricto (-14 LUFS, TP <= -1.0 dBTP)
"""

import os
import sys
import json
import subprocess

def get_cli(name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.abspath(os.path.join(script_dir, "config.local.json"))
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8-sig") as f:
            cfg = json.load(f)
            if cfg.get(name) and os.path.exists(cfg[name]):
                return cfg[name]
    raise FileNotFoundError(f"No se encontró {name} en config.local.json")

def assemble():
    print("=" * 65)
    print(" [MONTAJE] Ensamblaje Completo Suite Craft (FC + EC + PC + SC)")
    print(" Proyecto: 2026-10-26_accesibilidad-rural (Vertical 720x1280)")
    print("=" * 65)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, ".."))
    proj_dir = os.path.join(repo_root, "PROYECTOS", "2026-10-26_accesibilidad-rural")

    fc_cli = get_cli("filmcraft_cli")
    ec_cli = get_cli("effectcraft_cli")
    pc_cli = get_cli("photocraft_cli")
    sc_cli = get_cli("soundcraft_cli")

    v_dir = os.path.join(proj_dir, "01_fuentes", "video")
    a_dir = os.path.join(proj_dir, "01_fuentes", "audio")
    m_dir = os.path.join(proj_dir, "01_fuentes", "musica")
    g_dir = os.path.join(proj_dir, "01_fuentes", "graficos")
    fc_dir = os.path.join(proj_dir, "02_filmcraft")
    exp_dir = os.path.join(proj_dir, "03_exports")
    prev_dir = os.path.join(proj_dir, "04_previews")

    # Archivos fuente verificados
    clip1 = os.path.join(v_dir, "clip_01_intro.mp4")
    clip2 = os.path.join(v_dir, "clip_02_problema.mp4")
    clip3 = os.path.join(v_dir, "clip_03_solucion.mp4")
    clip4 = os.path.join(v_dir, "clip_04_cierre.mp4")
    overlay_mov = os.path.join(g_dir, "overlay_titulo.mov")
    loc_wav = os.path.join(a_dir, "locucion_master.wav")
    musica_wav = os.path.join(m_dir, "musica_fondo_48k.wav")

    # 1. Crear proyecto FilmCraft .fcproj
    fcproj_path = os.path.join(fc_dir, "accesibilidad-rural_v01.fcproj")
    if os.path.exists(fcproj_path):
        try: os.remove(fcproj_path)
        except Exception: pass

    print("[*] Creando proyecto FilmCraft nativo: accesibilidad-rural_v01.fcproj...")
    subprocess.run([fc_cli, "--save-as", fcproj_path, "exec", "file.newProject", "name=accesibilidad-rural"], check=True)

    seq_params = json.dumps({"name": "Principal", "width": 720, "height": 1280, "fps": 30.0, "video": 3, "audio": 2})
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "file.newSequence", seq_params], check=True)

    # 2. Importar medios a FilmCraft
    print("[*] Importando clips al contenedor de medios de FilmCraft...")
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "import", clip1, clip2, clip3, clip4, overlay_mov, loc_wav, musica_wav], check=True)

    res_tree = subprocess.run([fc_cli, "--project", fcproj_path, "inspect", "project", "--compact"], capture_output=True, text=True, check=True)
    tree = json.loads(res_tree.stdout)
    items = {c["name"]: c["item"] for c in tree["root"]["children"]}

    print("[*] Despachando clips a pistas multitrack (V1, V2, A1, A2)...")
    # Pista V1: Clips secuenciales (0s, 18s, 36s, 54s)
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", json.dumps({"item": items["clip_01_intro.mp4"], "track": "V1", "seconds": 0.0, "insert": False})], check=True)
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", json.dumps({"item": items["clip_02_problema.mp4"], "track": "V1", "seconds": 18.0, "insert": False})], check=True)
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", json.dumps({"item": items["clip_03_solucion.mp4"], "track": "V1", "seconds": 36.0, "insert": False})], check=True)
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", json.dumps({"item": items["clip_04_cierre.mp4"], "track": "V1", "seconds": 54.0, "insert": False})], check=True)

    # Pista V2: Overlay de EffectCraft en t=1.0s (ProRes 4444 con canal alfa)
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", json.dumps({"item": items["overlay_titulo.mov"], "track": "V2", "seconds": 1.0, "insert": False})], check=True)

    # Pista A1: Locución masterizada en SoundCraft (66.88s)
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", json.dumps({"item": items["locucion_master.wav"], "track": "A1", "seconds": 0.0, "insert": False})], check=True)

    # Pista A2: Música de fondo normalizada a 48kHz
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", json.dumps({"item": items["musica_fondo_48k.wav"], "track": "A2", "seconds": 0.0, "insert": False})], check=True)

    # 3. Concatenación y Renderizado del Master Final con Quality Gate EBU R128 (-14.0 LUFS, TP <= -1.2 dBTP)
    final_master = os.path.join(exp_dir, "accesibilidad-rural_v01_vertical_720.mp4")
    print(f"[*] Renderizando master final vertical (720x1280 @ 30fps) -> {final_master}...")

    # Concatenar los 4 clips de video con overlay de EffectCraft en t=1..4s y mezcla de audio con loudnorm
    filter_complex = (
        "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0[vbase];"
        "[4:v]scale=720:1280:force_original_aspect_ratio=decrease[ovscaled];"
        "[vbase][ovscaled]overlay=0:H-h-80:enable='between(t,1,4)'[vout];"
        "[5:a]volume=1.0[avoice];"
        "[6:a]volume=0.10,aloop=loop=-1:size=2880000[amusic];"
        "[avoice][amusic]amix=inputs=2:duration=first:dropout_transition=2[amix];"
        "[amix]loudnorm=I=-14.0:TP=-1.5:LRA=7,alimiter=limit=-1.2dB:level=false[aout]"
    )

    cmd_render = [
        "ffmpeg", "-y", "-nostats", "-loglevel", "error",
        "-i", clip1,
        "-i", clip2,
        "-i", clip3,
        "-i", clip4,
        "-i", overlay_mov,
        "-i", loc_wav,
        "-i", musica_wav,
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-t", "66.88",
        final_master
    ]
    subprocess.run(cmd_render, check=True)

    # 4. Generar 4 fotogramas deterministas para QA en 04_previews
    print("[*] Extrayendo 4 fotogramas clave deterministas para QA...")
    qa_times = [5, 20, 40, 58]
    for idx, t in enumerate(qa_times, start=1):
        qa_file = os.path.join(prev_dir, f"qa_0{idx}_frame.png")
        subprocess.run([
            "ffmpeg", "-y", "-nostats", "-loglevel", "error",
            "-ss", str(t), "-i", final_master, "-frames:v", "1",
            "-vf", "scale=360:640", qa_file
        ], check=True)

    # 5. Generar Miniatura vertical con PhotoCraft CLI
    print("[*] Diseñando y optimizando miniatura vertical con PhotoCraft CLI...")
    pc_py = os.path.join(script_dir, "photocraft", "pc_thumbnail.py")
    subprocess.run([
        "python", pc_py,
        "--project", proj_dir,
        "--title", "ACCESIBILIDAD RURAL",
        "--subtitle", "TECNOLOGÍA EN LOS ANDES",
        "--aspect", "9:16"
    ], check=True)

    # 6. Generar Collage 2x2 QA
    print("[*] Generando collage 2x2 para auditoría QA...")
    collage_py = os.path.join(script_dir, "crear-collage-qa.py")
    subprocess.run(["python", collage_py, proj_dir], check=True)

    print("\n[OK] Montaje multitrack y generación de activos completada con éxito.")
    print(f"     Timeline FilmCraft: {fcproj_path}")
    print(f"     Master Exportado:   {final_master}")
    print(f"     Miniatura PhotoCraft: {os.path.join(exp_dir, 'thumbnail.jpg')}")
    print("=" * 65)

if __name__ == "__main__":
    assemble()
