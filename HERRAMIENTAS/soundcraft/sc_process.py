#!/usr/bin/env python3
"""
sc_process.py - Procesador y Masterizador de Audio con SoundCraft CLI
Normaliza, resamplea a 48000 Hz estéreo con dither profesional e inspecciona
archivos de audio y stems emitiendo manifiestos criptográficos SHA-256.
"""

import os
import sys
import json
import hashlib
import argparse
import subprocess

def get_soundcraft_cli():
    # 1. Variable de entorno
    cli = os.environ.get("SOUNDCRAFT_CLI")
    if cli and os.path.exists(cli):
        return cli
    
    # 2. Config local
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(script_dir, "..", "config.local.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                cand = cfg.get("soundcraft_cli")
                if cand and os.path.exists(cand):
                    return cand
        except Exception:
            pass

    # 3. Rutas por defecto
    user_home = os.environ.get("USERPROFILE", "")
    cand = os.path.join(user_home, ".gemini", "antigravity", "scratch", "craft_tools", "soundcraft", "soundcraft-0.13.1-windows-x64-portable", "soundcraft-cli.exe")
    if os.path.exists(cand):
        return cand
    
    return "soundcraft-cli.exe"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def inspect_audio(filepath, sc_cli=None):
    if not sc_cli:
        sc_cli = get_soundcraft_cli()
    
    cmd = [sc_cli, "info", os.path.abspath(filepath)]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        try:
            return json.loads(res.stdout)
        except Exception:
            pass
    return None

def process_audio(input_file, output_file=None, rate=48000, bit_depth=24, normalize=True):
    sc_cli = get_soundcraft_cli()
    abs_in = os.path.abspath(input_file)
    if not os.path.exists(abs_in):
        raise FileNotFoundError(f"Archivo de audio no encontrado: {abs_in}")

    if not output_file:
        base, ext = os.path.splitext(abs_in)
        output_file = f"{base}_sc_master{ext}"
    abs_out = os.path.abspath(output_file)
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)

    print(f"[*] Analizando audio original con SoundCraft CLI...")
    info_before = inspect_audio(abs_in, sc_cli)
    if info_before:
        print(f"    Formato actual: {info_before.get('channels')} ch, {info_before.get('sample_rate')} Hz, {info_before.get('seconds')}s, {info_before.get('sample_format')}")

    print(f"[*] Procesando y normalizando audio hacia: {os.path.basename(abs_out)}...")
    cmd = [sc_cli, "convert", abs_in, abs_out, "--rate", str(rate), "--bit-depth", str(bit_depth)]
    if normalize:
        cmd.append("--normalize")

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0 or not os.path.exists(abs_out):
        raise RuntimeError(f"Fallo en SoundCraft CLI convert: {res.stderr.strip() or res.stdout.strip()}")

    info_after = inspect_audio(abs_out, sc_cli) or {}
    sha256_hash = sha256_file(abs_out)
    size_bytes = os.path.getsize(abs_out)

    manifest = {
        "status": "ok",
        "engine": "SoundCraft CLI 0.13.1",
        "input_file": os.path.basename(abs_in),
        "output_file": os.path.basename(abs_out),
        "output_path": abs_out,
        "sample_rate": info_after.get("sample_rate", rate),
        "channels": info_after.get("channels", 2),
        "seconds": info_after.get("seconds"),
        "sample_format": info_after.get("sample_format", f"Int{bit_depth}"),
        "size_bytes": size_bytes,
        "sha256": sha256_hash
    }

    manifest_path = os.path.join(os.path.dirname(abs_out), "audio-manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[OK] Audio procesado exitosamente con SoundCraft: {abs_out}")
    print(f"     Sample Rate: {manifest['sample_rate']} Hz | Formato: {manifest['sample_format']}")
    print(f"     SHA-256: {sha256_hash}")
    print(f"     Manifiesto: {manifest_path}")
    return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Procesamiento y Normalización de Audio con SoundCraft CLI")
    parser.add_argument("input", help="Archivo de audio de entrada")
    parser.add_argument("--out", help="Archivo de salida")
    parser.add_argument("--rate", type=int, default=48000, help="Frecuencia de muestreo (default: 48000 Hz)")
    parser.add_argument("--bit-depth", type=int, default=24, choices=[16, 24, 32], help="Profundidad de bits (default: 24)")
    parser.add_argument("--no-normalize", action="store_true", help="Desactivar normalizacion")
    
    args = parser.parse_args()
    process_audio(args.input, args.out, rate=args.rate, bit_depth=args.bit_depth, normalize=not args.no_normalize)
