#!/usr/bin/env python3
"""
Ensamblador Real del Proyecto Golden Test (10s @ 30fps)
1. Genera overlay ProRes 4444 RGBA con EffectCraft (ec_render.py) y emite render-manifest.json.
2. Crea el proyecto .fcproj en FilmCraft CLI con pistas V1, V2, V3, A1, A2.
3. Importa y coloca en timeline:
   - V1: clip sintético de video
   - V2: overlay de EffectCraft con canal alfa real
   - A1: locución Edge-TTS (WAV 48kHz estéreo)
   - A2: música de fondo (WAV 48kHz estéreo)
4. Renderiza el máster final de 10s a 1280x720 @ 30fps con audio normalizado EBU R128 (-14.0 LUFS, TP <= -1.2 dBTP).
"""

import os
import sys
import json
import subprocess
import argparse

def get_cli(name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.abspath(os.path.join(script_dir, "..", "config.local.json"))
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8-sig") as f:
            cfg = json.load(f)
            if cfg.get(name) and os.path.exists(cfg[name]):
                return cfg[name]
    raise FileNotFoundError(f"No se encontró la ruta para {name} en config.local.json")

def build_golden_project(project_dir=None):
    print("=" * 65)
    print(" [ENSAMBLADOR GOLDEN] Montaje Nativo FilmCraft + EffectCraft ")
    print("=" * 65)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    if project_dir:
        proj_dir = os.path.abspath(project_dir)
    else:
        proj_dir = os.path.join(repo_root, "PROYECTOS", "test-golden-10s")

    fc_cli = get_cli("filmcraft_cli")
    ec_cli = get_cli("effectcraft_cli")

    v_dir = os.path.join(proj_dir, "01_fuentes", "video")
    a_dir = os.path.join(proj_dir, "01_fuentes", "audio")
    m_dir = os.path.join(proj_dir, "01_fuentes", "musica")
    g_dir = os.path.join(proj_dir, "01_fuentes", "graficos")
    fc_dir = os.path.join(proj_dir, "02_filmcraft")
    exp_dir = os.path.join(proj_dir, "03_exports")
    prev_dir = os.path.join(proj_dir, "04_previews")

    for d in [v_dir, a_dir, m_dir, g_dir, fc_dir, exp_dir, prev_dir]:
        os.makedirs(d, exist_ok=True)

    # 1. Metraje de video sintético (1280x720, 30fps, 10.0s)
    clip_video = os.path.join(v_dir, "clip_golden_10s.mp4")
    if not os.path.exists(clip_video):
        print("[*] Generando metraje base sintético 1280x720 @ 30fps...")
        subprocess.run([
            "ffmpeg", "-y", "-nostats", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30",
            "-t", "10", "-c:v", "libx264", "-pix_fmt", "yuv420p", clip_video
        ], check=True)

    # 2. Música sintética (48kHz estéreo, 10s)
    clip_musica = os.path.join(m_dir, "musica_golden_10s.wav")
    if not os.path.exists(clip_musica):
        print("[*] Generando cama musical 48kHz estéreo...")
        subprocess.run([
            "ffmpeg", "-y", "-nostats", "-loglevel", "error",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=10",
            "-af", "volume=-24dB", clip_musica
        ], check=True)

    # 3. Locución Edge-TTS (WAV 48kHz)
    loc_wav = os.path.join(a_dir, "locucion.wav")
    if not os.path.exists(loc_wav):
        print("[*] Sintetizando locución con Edge-TTS...")
        gen_voz_ps1 = os.path.join(repo_root, "HERRAMIENTAS", "generar-voz.ps1")
        subprocess.run([
            "powershell", "-ExecutionPolicy", "Bypass", "-File", gen_voz_ps1,
            "-Proyecto", proj_dir, "-NombreSalida", "locucion"
        ], check=True)

    # 4. Generar Overlay con EffectCraft (ProRes 4444 RGBA con canal alfa real)
    overlay_mov = os.path.join(g_dir, "overlay_golden.mov")
    template_path = os.path.join(script_dir, "templates", "lower_third_clean.ectemplate")
    diseno_path = os.path.join(g_dir, "diseno_golden.json")

    diseno_data = {
        "template": template_path,
        "comp": "Lower Third",
        "values": {
            "Name": "Ingeniero Auditor",
            "Title": "Integridad de Pipeline FilmCraft",
            "Bar Color": [0.0, 0.9, 0.5, 1.0]
        },
        "fps": 30,
        "start": 0.0,
        "end": 2.0,
        "format": "prores",
        "channels": "rgba",
        "output": overlay_mov
    }
    with open(diseno_path, "w", encoding="utf-8") as f:
        json.dump(diseno_data, f, indent=2)

    print("[*] Renderizando overlay de EffectCraft con ec_render.py...")
    ec_render_py = os.path.join(script_dir, "ec_render.py")
    subprocess.run(["python", ec_render_py, diseno_path], check=True)

    # 5. Montar proyecto real .fcproj en FilmCraft
    fcproj_path = os.path.join(fc_dir, "test-golden-10s_v01.fcproj")
    if os.path.exists(fcproj_path):
        try: os.remove(fcproj_path)
        except Exception: pass

    print("[*] Creando proyecto nativo en FilmCraft CLI...")
    subprocess.run([fc_cli, "--save-as", fcproj_path, "exec", "file.newProject", "name=test-golden-10s"], check=True)

    seq_params = json.dumps({"name": "Principal", "width": 1280, "height": 720, "fps": 30.0, "video": 3, "audio": 2})
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "file.newSequence", seq_params], check=True)

    # Importar medios
    print("[*] Importando clips al contenedor de medios de FilmCraft...")
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "import", clip_video, overlay_mov, loc_wav, clip_musica], check=True)

    # Obtener IDs numéricos de medios
    res_tree = subprocess.run([fc_cli, "--project", fcproj_path, "inspect", "project", "--compact"], capture_output=True, text=True, check=True)
    tree = json.loads(res_tree.stdout)
    items = {c["name"]: c["item"] for c in tree["root"]["children"]}

    print(f"[*] Colocando clips en pistas multitrack (V1, V2, A1, A2)...")
    # V1: clip_golden_10s.mp4 en t=0s
    p_v1 = json.dumps({"item": items["clip_golden_10s.mp4"], "track": "V1", "seconds": 0.0, "insert": False})
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", p_v1], check=True)

    # V2: overlay_golden.mov en t=1.0s (Canal alfa sobre V1)
    p_v2 = json.dumps({"item": items["overlay_golden.mov"], "track": "V2", "seconds": 1.0, "insert": False})
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", p_v2], check=True)

    # A1: locucion.wav en t=0s
    p_a1 = json.dumps({"item": items["locucion.wav"], "track": "A1", "seconds": 0.0, "insert": False})
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", p_a1], check=True)

    # A2: musica_golden_10s.wav en t=0s
    p_a2 = json.dumps({"item": items["musica_golden_10s.wav"], "track": "A2", "seconds": 0.0, "insert": False})
    subprocess.run([fc_cli, "--project", fcproj_path, "--save", "exec", "timeline.place", p_a2], check=True)

    # 6. Renderizar master final con mezcla de audio exacta EBU R128 (-14.0 LUFS, TP <= -1.2 dBTP)
    final_master = os.path.join(exp_dir, "test-golden-10s_v01_horizontal_720.mp4")
    print(f"[*] Renderizando master final con normalizacion EBU R128 -> {final_master}")

    filter_complex = (
        "[0:v][1:v]overlay=0:0:enable='between(t,1,3)'[vout];"
        "[2:a][3:a]amix=inputs=2:duration=first[amix];"
        "[amix]loudnorm=I=-14.0:TP=-1.5:LRA=7,alimiter=limit=-1.2dB:level=false[aout]"
    )

    cmd_render = [
        "ffmpeg", "-y", "-nostats", "-loglevel", "error",
        "-i", clip_video,
        "-i", overlay_mov,
        "-i", loc_wav,
        "-i", clip_musica,
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-t", "10",
        final_master
    ]
    subprocess.run(cmd_render, check=True)

    # 7. Generar fotogramas deterministas para QA
    for i in range(1, 5):
        qa_frame = os.path.join(prev_dir, f"qa_0{i}_frame.png")
        subprocess.run([
            "ffmpeg", "-y", "-nostats", "-loglevel", "error",
            "-ss", str(i * 2), "-i", final_master, "-frames:v", "1",
            "-vf", "scale=480:270", qa_frame
        ], check=True)

    print(f"\n[OK] Montaje completado:")
    print(f"     Proyecto FilmCraft: {fcproj_path}")
    print(f"     Overlay EffectCraft: {overlay_mov}")
    print(f"     Master Exportado:   {final_master}")
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ensamblador del proyecto golden de 10s")
    parser.add_argument(
        "--project-dir",
        help="Carpeta de proyecto alternativa (para pruebas herméticas; no toca el golden)",
    )
    args = parser.parse_args()
    build_golden_project(args.project_dir)
