#!/usr/bin/env python3
"""
rem_render.py
Motor de Renderizado y Validacion Criptografica de Remotion para EditorVideo.
Permite renderizar composiciones React (subtítulos cinéticos, infografías, rótulos)
en ProRes 4444 RGBA (con canal alfa real) o MP4 H.264, verifica las especificaciones
con ffprobe y emite render-manifest.json firmado con SHA-256.
"""

import os
import sys
import json
import re
import hashlib
import subprocess
import argparse
from datetime import datetime, timezone

def get_remotion_cli():
    # 1. Variable de entorno
    env_cli = os.environ.get("REMOTION_CLI")
    if env_cli:
        return env_cli

    # 2. Local node_modules en HERRAMIENTAS/remotion
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "node_modules", ".bin", "remotion.cmd"),
        os.path.join(script_dir, "node_modules", ".bin", "remotion"),
        os.path.join(script_dir, "..", "..", "node_modules", ".bin", "remotion.cmd"),
    ]
    for cand in candidates:
        if os.path.exists(cand):
            return cand

    # 3. Fallback a npx remotion
    return "npx remotion"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def parse_time_to_seconds(time_str):
    # Formato SRT: 00:01:23,456
    time_str = time_str.replace(",", ".")
    parts = time_str.split(":")
    hours = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds

def parse_srt_to_cues(srt_path, fps=30):
    if not os.path.exists(srt_path):
        raise FileNotFoundError(f"No existe el archivo SRT: {srt_path}")

    with open(srt_path, "r", encoding="utf-8-sig") as f:
        content = f.read()

    blocks = re.split(r"\n\s*\n", content.strip())
    cues = []
    
    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if len(lines) < 2:
            continue
            
        # Determinar si la primera linea es un indice o timecode
        time_line_idx = 1 if re.match(r"^\d+$", lines[0]) else 0
        if time_line_idx >= len(lines):
            continue
            
        time_line = lines[time_line_idx]
        text_lines = lines[time_line_idx + 1 :]
        text = " ".join(text_lines)

        time_match = re.search(
            r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})",
            time_line,
        )
        if not time_match:
            continue

        start_sec = parse_time_to_seconds(time_match.group(1))
        end_sec = parse_time_to_seconds(time_match.group(2))

        start_frame = int(round(start_sec * fps))
        end_frame = int(round(end_sec * fps))

        # Crear palabras individuales con distribucion equitativa de tiempo
        raw_words = text.split()
        words = []
        if raw_words:
            total_duration = max(1, end_frame - start_frame)
            word_dur = total_duration / len(raw_words)
            for i, w in enumerate(raw_words):
                w_start = int(start_frame + i * word_dur)
                w_end = int(start_frame + (i + 1) * word_dur)
                words.append({"text": w, "startFrame": w_start, "endFrame": w_end})

        cues.append({
            "id": len(cues) + 1,
            "startFrame": start_frame,
            "endFrame": end_frame,
            "text": text,
            "words": words,
        })

    return cues

def probe_video(video_path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,pix_fmt,duration,nb_frames",
        "-of", "json",
        video_path,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        raise RuntimeError(f"Error inspeccionando salida con ffprobe: {res.stderr}")
    
    data = json.loads(res.stdout)
    streams = data.get("streams", [])
    if not streams:
        raise ValueError(f"No se detecto stream de video en {video_path}")
        
    s = streams[0]
    r_fps = s.get("r_frame_rate", "30/1")
    try:
        if "/" in r_fps:
            num, den = r_fps.split("/")
            fps_val = float(num) / float(den) if float(den) > 0 else 30.0
        else:
            fps_val = float(r_fps)
    except Exception:
        fps_val = 30.0

    pix_fmt = s.get("pix_fmt", "")
    has_alpha = ("a" in pix_fmt) or ("yuva" in pix_fmt) or ("rgba" in pix_fmt)

    return {
        "width": int(s.get("width", 0)),
        "height": int(s.get("height", 0)),
        "fps": round(fps_val, 2),
        "pix_fmt": pix_fmt,
        "has_alpha": has_alpha,
        "duration": float(s.get("duration", 0) or 0),
        "nb_frames": int(s.get("nb_frames", 0) or 0),
    }

def main():
    parser = argparse.ArgumentParser(description="Renderizador y Validador de Remotion para EditorVideo")
    parser.add_argument("--comp", required=True, help="Nombre de la composicion (ej. SubtitulosKineticVertical)")
    parser.add_argument("--output", required=True, help="Ruta del video resultante (.mov o .mp4)")
    parser.add_argument("--entry", default=None, help="Punto de entrada de Remotion (src/index.ts)")
    parser.add_argument("--props", default=None, help="JSON string o ruta a archivo JSON de props")
    parser.add_argument("--srt", default=None, help="Ruta a archivo .srt para autogenerar cues de subtitulos")
    parser.add_argument("--format", choices=["prores", "mp4"], default="prores", help="Formato de exportacion")
    parser.add_argument("--channels", choices=["rgba", "rgb"], default="rgba", help="Canales de color (rgba con alfa)")
    parser.add_argument("--fps", type=int, default=30, help="Frames por segundo")
    parser.add_argument("--frames", default=None, help="Rango de frames a renderizar (ej. 0-150)")
    parser.add_argument("--project", default=None, help="Carpeta del proyecto para contexto de salida")

    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    entry_point = args.entry or os.path.join(script_dir, "src", "index.ts")

    output_path = os.path.abspath(args.output)
    out_dir = os.path.dirname(output_path)
    os.makedirs(out_dir, exist_ok=True)

    remotion_cli = get_remotion_cli()

    print("=" * 65)
    print(" [REMOTION] Motor de Render y Validacion Criptografica")
    print(f" Composicion: {args.comp}")
    print(f" Formato:     {args.format.upper()} ({args.channels.upper()})")
    print(f" Salida:      {output_path}")
    print("=" * 65)

    # 1. Preparar Props
    props_dict = {}
    if args.props:
        if os.path.exists(args.props):
            with open(args.props, "r", encoding="utf-8-sig") as f:
                props_dict = json.load(f)
        else:
            try:
                props_dict = json.loads(args.props)
            except Exception as e:
                raise ValueError(f"No se pudo parsear --props como JSON: {e}")

    # Si se pasó un SRT, convertir a cues y mezclar con props
    if args.srt:
        print(f"[*] Parseando subtitulos SRT desde: {args.srt}")
        cues = parse_srt_to_cues(args.srt, fps=args.fps)
        props_dict["cues"] = cues
        print(f"[*] Total de bloques de subtitulo cargados: {len(cues)}")

    # Guardar props temporales si existen
    props_temp_path = None
    if props_dict:
        props_temp_path = os.path.join(out_dir, f"props_temp_{args.comp}.json")
        with open(props_temp_path, "w", encoding="utf-8") as f:
            json.dump(props_dict, f, ensure_ascii=False, indent=2)

    # 2. Construir comando de render de Remotion
    cmd = [
        remotion_cli,
        "render",
        entry_point,
        args.comp,
        output_path,
        "--log=info",
    ]

    if args.format == "prores" and args.channels == "rgba":
        cmd.extend([
            "--codec=prores",
            "--prores-profile=4444",
            "--pixel-format=yuva444p10le",
            "--image-format=png",
        ])
    elif args.format == "mp4":
        cmd.extend([
            "--codec=h264",
        ])

    if props_temp_path:
        cmd.append(f"--props={props_temp_path}")

    if args.frames:
        cmd.append(f"--frames={args.frames}")

    print(f"[*] Ejecutando renderizado con Remotion...")
    print(f"    Comando: {' '.join(cmd)}")
    
    # Ejecutar en el directorio de remotion para resolver node_modules correctamente
    render_res = subprocess.run(
        cmd,
        cwd=script_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=True if remotion_cli.endswith(".cmd") or "npx" in remotion_cli else False,
    )

    # Limpiar props temporales
    if props_temp_path and os.path.exists(props_temp_path):
        try:
            os.remove(props_temp_path)
        except Exception:
            pass

    if render_res.returncode != 0:
        print("[ERROR FATAL] Fallo en renderizado de Remotion:")
        print(render_res.stderr)
        print(render_res.stdout)
        sys.exit(1)

    # 3. Validar existencia y especificaciones del archivo resultante
    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        print(f"[ERROR FATAL] No se genero el archivo de video: {output_path}")
        sys.exit(1)

    print("[*] Verificando especificaciones tecnicas con ffprobe...")
    info = probe_video(output_path)
    file_sha256 = sha256_file(output_path)

    # Comprobación estricta de canal alfa si se requería RGBA
    if args.channels == "rgba" and not info["has_alpha"]:
        print(f"[ERROR FATAL] Se solicito canal alfa (RGBA) pero el formato de pixel es '{info['pix_fmt']}' (sin canal alfa).")
        sys.exit(1)

    # 4. Generar manifiesto criptográfico
    manifest = {
        "status": "ok",
        "engine": "Remotion 4.0.539",
        "composition": args.comp,
        "output_file": os.path.basename(output_path),
        "full_path": output_path,
        "sha256": file_sha256,
        "width": info["width"],
        "height": info["height"],
        "fps": info["fps"],
        "pix_fmt": info["pix_fmt"],
        "has_alpha": info["has_alpha"],
        "duration_seconds": info["duration"],
        "frames": info["nb_frames"],
        "format": args.format,
        "channels": args.channels,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    manifest_general = os.path.join(out_dir, "render-manifest.json")
    manifest_specific = os.path.join(out_dir, f"render-manifest-{args.comp}.json")

    with open(manifest_general, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    with open(manifest_specific, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("\n[OK] Renderizado completado exitosamente y manifest emitido:")
    print(f"     Archivo:   {output_path}")
    print(f"     SHA256:    {file_sha256}")
    print(f"     Alfa (a):  {info['has_alpha']} (pix_fmt: {info['pix_fmt']})")
    print(f"     Res:       {info['width']}x{info['height']} @ {info['fps']} fps")
    print(f"     Manifest:  {manifest_general}")
    print(f"     Especif.:  {manifest_specific}")
    print("=" * 65)

if __name__ == "__main__":
    main()
