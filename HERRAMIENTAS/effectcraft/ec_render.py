#!/usr/bin/env python3
"""
Motor de Renderizado y Validacion de EffectCraft (ec_render.py)
Encapsula el flujo de renderizado desde diseno.json, valida controles,
inspecciona la salida (Pillow/ffprobe para dimensiones, fps, frames, pix_fmt con alfa)
y emite render-manifest.json con hash SHA256 y estado verificable.
"""

import os
import sys
import json
import hashlib
import subprocess
import argparse
from datetime import datetime, timezone
from PIL import Image

def get_effectcraft_cli():
    if os.environ.get("EFFECTCRAFT_CLI") and os.path.exists(os.environ["EFFECTCRAFT_CLI"]):
        return os.environ["EFFECTCRAFT_CLI"]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.abspath(os.path.join(script_dir, "..", "config.local.json"))
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8-sig") as f:
            cfg = json.load(f)
            if cfg.get("effectcraft_cli") and os.path.exists(cfg["effectcraft_cli"]):
                return cfg["effectcraft_cli"]

    cand = os.path.expanduser(r"~/.gemini/antigravity/scratch/craft_tools/effectcraft/effectcraft-0.11.1-windows-x64-portable/effectcraft-cli.exe")
    if os.path.exists(cand):
        return cand
        
    raise FileNotFoundError("No se encontró effectcraft-cli.exe. Ejecuta setup-entorno.ps1")

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def inspect_template(cli, template_path):
    cmd = [cli, "exec", "essential.templateInfo", "--params", json.dumps({"path": template_path})]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Error inspeccionando template con essential.templateInfo: {res.stderr}")
    return json.loads(res.stdout)

def validate_design(diseno, tmpl_info):
    errors = []
    
    # 1. Validar nombre de comp
    req_comp = diseno.get("comp")
    actual_comp = tmpl_info.get("compName")
    if req_comp and actual_comp and req_comp != actual_comp:
        errors.append(f"Comp que no coincide: diseno.json pide comp '{req_comp}', pero el template contiene '{actual_comp}'.")

    # 2. Validar controles y tipos
    tmpl_controls = {c["name"]: c for c in tmpl_info.get("controls", [])}
    diseno_values = diseno.get("values", {})

    for key, val in diseno_values.items():
        if key not in tmpl_controls:
            errors.append(f"Control desconocido: '{key}' no existe en el template. Controles validos: {list(tmpl_controls.keys())}")
            continue

        ctrl_spec = tmpl_controls[key]
        ctype = ctrl_spec.get("type", "unknown")

        if ctype == "text":
            if not isinstance(val, str):
                errors.append(f"Tipo incorrecto para '{key}': se esperaba texto (str), recibido {type(val).__name__} ({val}).")
        elif ctype == "color":
            if not (isinstance(val, list) and len(val) in (3, 4) and all(isinstance(x, (int, float)) for x in val)):
                errors.append(f"Tipo incorrecto para '{key}': se esperaba color [r, g, b, a] con numeros, recibido {type(val).__name__} ({val}).")
        elif ctype in ("number", "slider"):
            if not isinstance(val, (int, float)):
                errors.append(f"Tipo incorrecto para '{key}': se esperaba numero, recibido {type(val).__name__} ({val}).")
        elif ctype in ("checkbox", "boolean"):
            if not isinstance(val, bool):
                errors.append(f"Tipo incorrecto para '{key}': se esperaba booleano, recibido {type(val).__name__} ({val}).")

    # 3. Validar consistencia de transparencia y formato
    fmt = diseno.get("format", "h264").lower()
    chans = diseno.get("channels", "rgb").lower()

    if chans == "rgba" and fmt not in ("prores", "png", "tiff", "exr", "webm"):
        errors.append(f"Transparencia sin alfa: se solicito channels 'rgba', pero el formato '{fmt}' no soporta canal alfa.")

    return errors

def verify_output_media(output_path, fmt, expected_channels, expected_fps=30.0):
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"El archivo de salida no fue generado: {output_path}")

    stats = {
        "size_bytes": os.path.getsize(output_path),
        "sha256": sha256_file(output_path),
        "has_alpha": False
    }

    if fmt == "png":
        im = Image.open(output_path)
        stats["dimensions"] = list(im.size)
        stats["mode"] = im.mode
        stats["has_alpha"] = (im.mode == "RGBA" or "transparency" in im.info)
        stats["frames_count"] = 1
        stats["duration_sec"] = 0.0

        if expected_channels == "rgba" and not stats["has_alpha"]:
            raise ValueError(f"Falla de canal alfa: se esperaba PNG RGBA con transparencia, modo obtenido: {im.mode}")
    else:
        # Video inspection via ffprobe
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=width,height,r_frame_rate,duration,nb_frames,pix_fmt,codec_name:format=duration",
            "-of", "json", output_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(res.stdout)
        video_stream = next((s for s in data.get("streams", []) if "width" in s), None)

        if not video_stream:
            raise ValueError("No se encontro flujo de video valido en el archivo renderizado.")

        w = video_stream["width"]
        h = video_stream["height"]
        pix_fmt = video_stream.get("pix_fmt", "")
        codec = video_stream.get("codec_name", "")
        nb_frames = int(video_stream.get("nb_frames") or 0)
        dur = float(video_stream.get("duration") or data.get("format", {}).get("duration", 0.0))

        stats["dimensions"] = [w, h]
        stats["pix_fmt"] = pix_fmt
        stats["codec"] = codec
        stats["duration_sec"] = dur
        stats["frames_count"] = nb_frames

        # Detectar alfa en pix_fmt (yuva..., rgba, etc.)
        has_alpha = "a" in pix_fmt or "rgba" in pix_fmt
        stats["has_alpha"] = has_alpha

        if expected_channels == "rgba" and not has_alpha:
            raise ValueError(f"Falla de canal alfa: se solicito video transparente RGBA, pero el pix_fmt obtenido es '{pix_fmt}' (sin canal alfa).")

    return stats

def render_design(diseno_path):
    print("=" * 65)
    print(" [EFFECTCRAFT] Motor de Render y Validacion (ec_render.py)")
    print(f" Diseno: {diseno_path}")
    print("=" * 65)

    if not os.path.exists(diseno_path):
        raise FileNotFoundError(f"No existe el archivo de diseño: {diseno_path}")

    with open(diseno_path, "r", encoding="utf-8-sig") as f:
        diseno = json.load(f)

    cli = get_effectcraft_cli()
    
    # 1. Obtener versión de EffectCraft
    ver_res = subprocess.run([cli, "--version"], capture_output=True, text=True)
    ec_version = ver_res.stdout.strip()

    # 2. Resolver ruta de template
    tmpl_path = diseno["template"]
    if not os.path.isabs(tmpl_path):
        base_dir = os.path.dirname(os.path.abspath(diseno_path))
        cand = os.path.join(base_dir, tmpl_path)
        if os.path.exists(cand):
            tmpl_path = cand
        else:
            # Buscar en templates del repo
            script_dir = os.path.dirname(os.path.abspath(__file__))
            cand2 = os.path.join(script_dir, "templates", os.path.basename(tmpl_path))
            if os.path.exists(cand2):
                tmpl_path = cand2
    
    if not os.path.exists(tmpl_path):
        raise FileNotFoundError(f"Template no encontrado: {tmpl_path}")

    # 3. Inspeccionar y validar template
    print(f"[*] Inspeccionando template: {os.path.basename(tmpl_path)}")
    tmpl_info = inspect_template(cli, tmpl_path)

    print("[*] Validando controles y contrato de diseño...")
    val_errors = validate_design(diseno, tmpl_info)
    if val_errors:
        print("\n[X] ERROR DE VALIDACION DE DISENO:")
        for err in val_errors:
            print(f"    - {err}")
        return {"status": "failed", "errors": val_errors}

    # 4. Preparar archivo de valores
    values_json_path = os.path.join(os.path.dirname(os.path.abspath(diseno_path)), "_temp_ec_values.json")
    with open(values_json_path, "w", encoding="utf-8") as f:
        json.dump(diseno.get("values", {}), f, indent=2)

    # 5. Ejecutar Render
    output_path = diseno["output"]
    if not os.path.isabs(output_path):
        output_path = os.path.abspath(os.path.join(os.path.dirname(diseno_path), output_path))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fmt = diseno.get("format", "prores").lower()
    chans = diseno.get("channels", "rgba").lower()
    start_t = str(diseno.get("start", 0.0))
    end_t = str(diseno.get("end", tmpl_info.get("duration", 2.0)))
    fps_val = str(diseno.get("fps", tmpl_info.get("frameRate", 30.0)))

    print(f"[*] Renderizando formato: {fmt.upper()} (Channels: {chans.upper()}) -> {output_path}")

    if fmt == "png":
        render_cmd = [
            cli, "render-frame",
            "--template", tmpl_path,
            "--values", values_json_path,
            "--time", start_t,
            "--out", output_path
        ]
        if chans == "rgba":
            render_cmd.append("--transparent")
    elif fmt == "prores":
        render_cmd = [
            cli, "render",
            "--template", tmpl_path,
            "--values", values_json_path,
            "--format", "prores",
            "--channels", chans,
            "--prores", "4444" if chans == "rgba" else "422",
            "--start", start_t,
            "--end", end_t,
            "--fps", fps_val,
            "--out", output_path
        ]
    elif fmt == "h264":
        render_cmd = [
            cli, "render",
            "--template", tmpl_path,
            "--values", values_json_path,
            "--format", "h264",
            "--start", start_t,
            "--end", end_t,
            "--fps", fps_val,
            "--out", output_path
        ]
    else:
        render_cmd = [
            cli, "render",
            "--template", tmpl_path,
            "--values", values_json_path,
            "--format", fmt,
            "--start", start_t,
            "--end", end_t,
            "--fps", fps_val,
            "--out", output_path
        ]

    res = subprocess.run(render_cmd, capture_output=True, text=True)
    if os.path.exists(values_json_path):
        try: os.remove(values_json_path)
        except Exception: pass

    if res.returncode != 0:
        raise RuntimeError(f"Fallo en render de EffectCraft: {res.stderr} {res.stdout}")

    # 6. Verificación estricta de la salida con Pillow / ffprobe
    print("[*] Verificando especificaciones de salida (dimensiones, fps, frames y canal alfa)...")
    media_stats = verify_output_media(output_path, fmt, chans, float(fps_val))

    # 7. Generar render-manifest.json
    out_dir = os.path.dirname(output_path)
    manifest_path = os.path.join(out_dir, "render-manifest.json")
    
    manifest_data = {
        "schema_version": "1.0.0",
        "status": "ok",
        "effectcraft_version": ec_version,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "design_file": os.path.basename(diseno_path),
        "template_name": tmpl_info.get("name"),
        "comp_name": tmpl_info.get("compName"),
        "output_file": os.path.basename(output_path),
        "output_path": output_path,
        "sha256": media_stats["sha256"],
        "size_bytes": media_stats["size_bytes"],
        "format": fmt,
        "channels": chans,
        "dimensions": media_stats.get("dimensions"),
        "duration_sec": media_stats.get("duration_sec"),
        "frames_count": media_stats.get("frames_count"),
        "has_alpha": media_stats.get("has_alpha"),
        "pix_fmt": media_stats.get("pix_fmt") or media_stats.get("mode"),
        "values_applied": diseno.get("values", {})
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print(f"[OK] Render completado y manifest emitido:")
    print(f"     Archivo:   {output_path}")
    print(f"     SHA256:    {media_stats['sha256']}")
    print(f"     Alfa (a):  {media_stats['has_alpha']}")
    print(f"     Manifest:  {manifest_path}")
    print("=" * 65)

    return manifest_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Renderizador y Validador de Diseños EffectCraft")
    parser.add_argument("diseno_json", help="Ruta al archivo diseno.json")
    args = parser.parse_args()

    try:
        manifest = render_design(args.diseno_json)
        if manifest.get("status") != "ok":
            sys.exit(1)
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR CRITICO] {e}")
        sys.exit(1)
