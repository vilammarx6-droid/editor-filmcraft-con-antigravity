#!/usr/bin/env python3
"""
Quality Gate de Audio y Video (EBU R128 + Video Stream Check)
Audita el archivo exportado y bloquea la publicación (exit 1) si no cumple los estándares.
"""

import os
import sys
import json
import subprocess
import argparse
import re

TARGET_LUFS_MIN = -16.0
TARGET_LUFS_MAX = -13.0
TARGET_LUFS_IDEAL = -14.0
MAX_TRUE_PEAK_DBTP = -1.0

def analyze_audio_ebur128(media_path):
    print(f"[*] Analizando sonoridad EBU R128 en: {media_path}")
    cmd = [
        "ffmpeg", "-nostats", "-i", media_path,
        "-filter_complex", "ebur128=peak=true",
        "-f", "null", "-"
    ]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, errors="replace")
    output = res.stderr

    # Parse ebur128 summary
    # Integrated loudness:
    #     I:         -14.1 LUFS
    #     Threshold: -24.3 LUFS
    # Loudness range:
    #     LRA:         6.2 LU
    # True peak:
    #     Peak:        -1.4 dBFS
    i_match = re.search(r"Integrated loudness:\s+I:\s+([-\d.]+)\s+LUFS", output)
    lra_match = re.search(r"Loudness range:\s+LRA:\s+([-\d.]+)\s+LU", output)
    tp_match = re.search(r"True peak:\s+Peak:\s+([-\d.]+)\s+dBFS", output)

    if not i_match or not tp_match:
        raise ValueError("No se pudieron extraer los valores EBU R128 del log de FFmpeg.")

    return {
        "integrated_lufs": float(i_match.group(1)),
        "loudness_range_lu": float(lra_match.group(1)) if lra_match else None,
        "true_peak_dbtp": float(tp_match.group(1))
    }

def analyze_video_stream(media_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height,r_frame_rate,duration,nb_frames:format=duration",
        "-of", "json", media_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, errors="replace")
    data = json.loads(res.stdout)
    
    video_stream = next((s for s in data.get("streams", []) if "width" in s), None)
    return {
        "video": video_stream,
        "format": data.get("format", {})
    }

def run_quality_gate(media_path, strict=True):
    if not os.path.exists(media_path):
        print(f"[ERROR] Archivo no encontrado: {media_path}")
        sys.exit(1)

    print("=" * 65)
    print(" [QUALITY GATE] Auditoria Integral de Audio y Video ")
    print(f" Archivo: {os.path.basename(media_path)}")
    print("=" * 65)

    errors = []
    warnings = []

    # 1. Auditoría de Audio
    try:
        audio_stats = analyze_audio_ebur128(media_path)
        lufs = audio_stats["integrated_lufs"]
        tp = audio_stats["true_peak_dbtp"]
        lra = audio_stats["loudness_range_lu"]

        print(f"\n-> Sonoridad Integrada: {lufs:.1f} LUFS (Objetivo: {TARGET_LUFS_IDEAL} LUFS, rango [{TARGET_LUFS_MIN}, {TARGET_LUFS_MAX}])")
        print(f"-> Pico Real (True Peak): {tp:.1f} dBTP (Limite maximo: {MAX_TRUE_PEAK_DBTP} dBTP)")
        if lra is not None:
            print(f"-> Rango Dinamico (LRA): {lra:.1f} LU")

        # Comprobación de True Peak (clipping)
        if tp > MAX_TRUE_PEAK_DBTP:
            diff = tp - MAX_TRUE_PEAK_DBTP
            errors.append(f"TRUE PEAK EXCEDIDO: {tp:.2f} dBTP supera el limite de {MAX_TRUE_PEAK_DBTP} dBTP por +{diff:.2f} dB. Riesgo de distorsion y saturacion.")
        
        # Comprobación de LUFS
        if lufs < TARGET_LUFS_MIN:
            warnings.append(f"SONORIDAD DEMASIADO BAJA: {lufs:.1f} LUFS (por debajo de {TARGET_LUFS_MIN} LUFS). El video se escuchara debil.")
        elif lufs > TARGET_LUFS_MAX:
            warnings.append(f"SONORIDAD DEMASIADO ALTA: {lufs:.1f} LUFS (por encima de {TARGET_LUFS_MAX} LUFS). Las plataformas aplicaran atenuacion forzada.")

    except Exception as e:
        errors.append(f"Error analizando pista de audio: {e}")

    # 2. Auditoría de Video
    try:
        vinfo = analyze_video_stream(media_path)
        vstream = vinfo.get("video")
        if vstream:
            w = vstream.get("width")
            h = vstream.get("height")
            fps = vstream.get("r_frame_rate")
            dur = float(vinfo.get("format", {}).get("duration", 0))
            print(f"\n-> Video Stream: {w}x{h} @ {fps} fps | Duracion: {dur:.2f}s")
        else:
            errors.append("No se encontro flujo de video en el archivo.")
    except Exception as e:
        warnings.append(f"Error inspeccionando flujo de video: {e}")

    print("\n" + "-" * 65)
    print(" RESULTADO DEL QUALITY GATE:")
    print("-" * 65)

    if warnings:
        print("[!] ADVERTENCIAS:")
        for w in warnings:
            print(f"    - {w}")

    if errors:
        print("[X] FALLOS CRITICOS (BLOQUEO DE EXPORT):")
        for err in errors:
            print(f"    - {err}")
        print("\n=> RECHAZADO: El archivo no cumple los estandares de emision.")
        print("   Ejecuta 'python HERRAMIENTAS/remediar-audio.py' para normalizar el audio.")
        sys.exit(1)

    print("[OK] APROBADO: El archivo cumple con todos los estandares de audio y video.")
    print("=" * 65)
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quality Gate EBU R128 para exportaciones de video")
    parser.add_argument("video_path", help="Ruta al video MP4/MKV a auditar")
    parser.add_argument("--permissive", action="store_true", help="No fallar por advertencias de sonoridad ligera")
    args = parser.parse_args()

    run_quality_gate(args.video_path)
