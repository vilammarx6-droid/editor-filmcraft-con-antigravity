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
    # 1. Variable de entorno (prioridad si está configurada)
    cli = os.environ.get("SOUNDCRAFT_CLI")
    if cli:
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

def process_audio(input_file, output_file=None, rate=48000, bit_depth=24, normalize=False, enforce_stereo=True):
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
    info_before = inspect_audio(abs_in, sc_cli) or {}
    ch_in = info_before.get("channels", 1)
    sr_in = info_before.get("sample_rate", 44100)
    print(f"    Formato actual: {ch_in} ch, {sr_in} Hz, {info_before.get('seconds')}s, {info_before.get('sample_format')}")

    # Si el audio es monoaural y se exige estéreo (estándar FilmCraft), duplicar a 2 canales
    source_to_convert = abs_in
    temp_stereo = None
    if enforce_stereo and ch_in == 1:
        print(f"[*] Canal mono detectado: expandiendo a 2 canales estéreo (FilmCraft standard)...")
        temp_stereo = abs_out + ".stereo_tmp.wav"
        res_mono = subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", abs_in,
            "-ac", "2",
            "-ar", str(rate),
            temp_stereo
        ], capture_output=True, text=True)
        if res_mono.returncode == 0 and os.path.exists(temp_stereo):
            source_to_convert = temp_stereo
        else:
            print(f"[!] Aviso: no se pudo expandir mono con ffmpeg, procediendo directo.")

    print(f"[*] Procesando con SoundCraft CLI hacia: {os.path.basename(abs_out)} (Target: {rate} Hz, {bit_depth}-bit)...")
    cmd = [sc_cli, "convert", source_to_convert, abs_out, "--rate", str(rate), "--bit-depth", str(bit_depth)]
    if normalize:
        print("[!] ADVERTENCIA: --normalize aplica normalizacion de pico (casi 0 dBTP). No usar para master EBU R128.")
        cmd.append("--normalize")

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if temp_stereo and os.path.exists(temp_stereo):
        try: os.remove(temp_stereo)
        except Exception: pass

    if res.returncode != 0 or not os.path.exists(abs_out):
        raise RuntimeError(f"Fallo en SoundCraft CLI convert: {res.stderr.strip() or res.stdout.strip()}")

    # Validar rigurosamente el archivo resultante con soundcraft-cli info
    info_after = inspect_audio(abs_out, sc_cli)
    if not info_after:
        raise RuntimeError(f"No se pudo inspeccionar el archivo de salida con SoundCraft CLI: {abs_out}")

    out_channels = info_after.get("channels", 0)
    out_rate = info_after.get("sample_rate", 0)

    if enforce_stereo and out_channels != 2:
        raise RuntimeError(f"Fallo de control de audio: El archivo resultante tiene {out_channels} canales (se exige estricto estéreo de 2 canales).")
    if out_rate != rate:
        raise RuntimeError(f"Fallo de control de audio: Frecuencia obtenida {out_rate} Hz no coincide con {rate} Hz.")

    sha256_hash = sha256_file(abs_out)
    size_bytes = os.path.getsize(abs_out)

    manifest = {
        "status": "ok",
        "engine": "SoundCraft CLI 0.13.1",
        "input_file": os.path.basename(abs_in),
        "output_file": os.path.basename(abs_out),
        "output_path": abs_out,
        "sample_rate": out_rate,
        "channels": out_channels,
        "seconds": info_after.get("seconds"),
        "sample_format": info_after.get("sample_format", f"Int{bit_depth}"),
        "size_bytes": size_bytes,
        "sha256": sha256_hash,
        "peak_normalized": normalize
    }

    out_dir = os.path.dirname(abs_out)
    base_name = os.path.splitext(os.path.basename(abs_out))[0]
    manifest_path = os.path.join(out_dir, "audio-manifest.json")
    manifest_specific_path = os.path.join(out_dir, f"audio-manifest-{base_name}.json")

    for m_path in (manifest_path, manifest_specific_path):
        with open(m_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[OK] Audio procesado y verificado con SoundCraft: {abs_out}")
    print(f"     Sample Rate: {out_rate} Hz | Canales: {out_channels} (Estéreo)")
    print(f"     SHA-256:     {sha256_hash}")
    print(f"     Manifest:    {manifest_path}")
    return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Procesamiento y Estandarización de Audio con SoundCraft CLI")
    parser.add_argument("input", help="Archivo de audio de entrada")
    parser.add_argument("--out", help="Archivo de salida")
    parser.add_argument("--rate", type=int, default=48000, help="Frecuencia de muestreo (default: 48000 Hz)")
    parser.add_argument("--bit-depth", type=int, default=24, choices=[16, 24, 32], help="Profundidad de bits (default: 24)")
    parser.add_argument("--normalize", action="store_true", help="Aplicar normalizacion de pico (advertencia: no cumple EBU R128)")
    
    args = parser.parse_args()
    try:
        process_audio(args.input, args.out, rate=args.rate, bit_depth=args.bit_depth, normalize=args.normalize)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
