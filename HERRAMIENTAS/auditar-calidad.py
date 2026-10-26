#!/usr/bin/env python3
"""
Quality Gate de Audio y Video (EBU R128 + Video/Audio Stream Verifier)
Audita el archivo exportado y bloquea la publicación (exit 1) si:
- La sonoridad integrada está fuera de [-16.0, -13.0] LUFS (Error estricto, no advertencia).
- El True Peak supera -1.0 dBTP (Clipping/distorsión).
- La frecuencia de muestreo del audio no es 48,000 Hz.
- La resolución o framerate no coinciden con los esperados.
"""

import os
import sys
import json
import subprocess
import argparse
import re
import math

TARGET_LUFS_MIN = -16.0
TARGET_LUFS_MAX = -13.0
TARGET_LUFS_IDEAL = -14.0
MAX_TRUE_PEAK_DBTP = -1.0
EXPECTED_SAMPLE_RATE = 48000

def analyze_audio_ebur128(media_path):
    cmd = [
        "ffmpeg", "-nostats", "-i", media_path,
        "-filter_complex", "ebur128=peak=true",
        "-f", "null", "-"
    ]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, errors="replace")
    output = res.stderr

    i_match = re.search(r"Integrated loudness:\s+I:\s+([-\d.]+|-\s*inf)\s+LUFS", output, re.IGNORECASE)
    lra_match = re.search(r"Loudness range:\s+LRA:\s+([-\d.]+|-\s*inf)\s+LU", output, re.IGNORECASE)
    tp_match = re.search(r"True peak:\s+Peak:\s+([-\d.]+|-\s*inf)\s+dBFS", output, re.IGNORECASE)

    if not i_match or not tp_match:
        raise ValueError("No se pudieron extraer los valores EBU R128 del log de FFmpeg.")

    def parse_ebur_val(val_str):
        if not val_str:
            return None
        v = val_str.strip().lower().replace(" ", "")
        if "inf" in v:
            return float("-inf")
        return float(v)

    return {
        "integrated_lufs": parse_ebur_val(i_match.group(1)),
        "loudness_range_lu": parse_ebur_val(lra_match.group(1)) if lra_match else None,
        "true_peak_dbtp": parse_ebur_val(tp_match.group(1))
    }

def analyze_media_streams(media_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_type,width,height,r_frame_rate,duration,nb_frames,sample_rate,channels:format=duration",
        "-of", "json", media_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, errors="replace")
    data = json.loads(res.stdout)
    
    video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    return {
        "video": video_stream,
        "audio": audio_stream,
        "format": data.get("format", {})
    }

def run_quality_gate(media_path, exp_w=None, exp_h=None, exp_fps=None):
    if not os.path.exists(media_path):
        print(f"[ERROR] Archivo no encontrado: {media_path}")
        sys.exit(1)

    print("=" * 65)
    print(" [QUALITY GATE ESTRICTO] Auditoria Integral de Audio y Video")
    print(f" Archivo: {os.path.basename(media_path)}")
    print("=" * 65)

    errors = []

    # 1. Auditoría de Audio EBU R128 (Estricta: Fuera de rango = ERROR)
    audio_stats = None
    try:
        audio_stats = analyze_audio_ebur128(media_path)
        lufs = audio_stats["integrated_lufs"]
        tp = audio_stats["true_peak_dbtp"]
        lra = audio_stats["loudness_range_lu"]

        lufs_str = "-inf" if math.isinf(lufs) else f"{lufs:.1f}"
        tp_str = "-inf" if math.isinf(tp) else f"{tp:.1f}"
        lra_str = "N/A" if lra is None or math.isinf(lra) else f"{lra:.1f}"

        print(f"-> Sonoridad Integrada: {lufs_str} LUFS (Objetivo: {TARGET_LUFS_IDEAL} LUFS, rango estricto [{TARGET_LUFS_MIN}, {TARGET_LUFS_MAX}])")
        print(f"-> Pico Real (True Peak): {tp_str} dBTP (Limite maximo: {MAX_TRUE_PEAK_DBTP} dBTP)")
        if lra is not None:
            print(f"-> Rango Dinamico (LRA): {lra_str} LU")

        # True Peak check
        if tp > MAX_TRUE_PEAK_DBTP:
            diff = tp - MAX_TRUE_PEAK_DBTP
            errors.append(f"TRUE PEAK EXCEDIDO: {tp_str} dBTP supera el limite de {MAX_TRUE_PEAK_DBTP} dBTP por +{diff:.2f} dB.")

        # LUFS range check (ERROR ESTRICTO, NO ADVERTENCIA)
        if math.isinf(lufs) or lufs < TARGET_LUFS_MIN:
            errors.append(f"SONORIDAD FUERA DE NORMA: {lufs_str} LUFS esta por debajo del minimo requerido ({TARGET_LUFS_MIN} LUFS).")
        elif lufs > TARGET_LUFS_MAX:
            errors.append(f"SONORIDAD FUERA DE NORMA: {lufs_str} LUFS supera el maximo permitido ({TARGET_LUFS_MAX} LUFS).")

    except Exception as e:
        errors.append(f"Error analizando pista de audio EBU R128: {e}")

    # 2. Auditoría de Flujos (Streams)
    try:
        streams = analyze_media_streams(media_path)
        vstream = streams.get("video")
        astream = streams.get("audio")
        fmt = streams.get("format", {})

        if not vstream:
            errors.append("No se encontro flujo de video en el archivo.")
        else:
            w = int(vstream["width"])
            h = int(vstream["height"])
            r_fps = str(vstream.get("r_frame_rate", "0/0"))
            if "/" in r_fps:
                parts = r_fps.split("/")
                try:
                    num, den = float(parts[0]), float(parts[1])
                    fps_eval = (num / den) if den > 0 else float(vstream.get("avg_frame_rate", 0))
                except Exception:
                    fps_eval = float(vstream.get("avg_frame_rate", 0))
            else:
                try:
                    fps_eval = float(r_fps)
                except Exception:
                    fps_eval = 0.0
            dur = float(fmt.get("duration", 0))
            print(f"-> Video Stream: {w}x{h} @ {fps_eval:.2f} fps | Duracion: {dur:.2f}s")

            if exp_w and w != exp_w: errors.append(f"Ancho no coincide: esperado {exp_w}, obtenido {w}")
            if exp_h and h != exp_h: errors.append(f"Alto no coincide: esperado {exp_h}, obtenido {h}")
            if exp_fps and abs(fps_eval - exp_fps) > 0.1: errors.append(f"Framerate no coincide: esperado {exp_fps}, obtenido {fps_eval}")

        if not astream:
            errors.append("No se encontro flujo de audio en el archivo.")
        else:
            sr = int(astream.get("sample_rate", 0))
            ch = int(astream.get("channels", 0))
            print(f"-> Audio Stream: {sr} Hz | Canales: {ch}")
            if sr != EXPECTED_SAMPLE_RATE:
                errors.append(f"Frecuencia de muestreo incorrecta: esperado {EXPECTED_SAMPLE_RATE} Hz (FilmCraft Standard), obtenido {sr} Hz.")

    except Exception as e:
        errors.append(f"Error inspeccionando flujos multimedia: {e}")

    print("\n" + "-" * 65)
    print(" RESULTADO DEL QUALITY GATE:")
    print("-" * 65)

    if errors:
        print("[X] FALLOS CRITICOS ENCONTRADOS (BLOQUEO DE EXPORT):")
        for err in errors:
            print(f"    - {err}")
        print("\n=> RECHAZADO: El archivo no cumple con los estandares estrictos de emision.")
        sys.exit(1)

    print("[OK] APROBADO: El archivo cumple estrictamente todos los estandares de audio y video.")
    print("==========================================================")
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quality Gate Estricto EBU R128")
    parser.add_argument("video_path", help="Ruta al video MP4 a auditar")
    parser.add_argument("--width", type=int, default=None, help="Ancho esperado")
    parser.add_argument("--height", type=int, default=None, help="Alto esperado")
    parser.add_argument("--fps", type=float, default=None, help="FPS esperado")
    args = parser.parse_args()

    run_quality_gate(args.video_path, args.width, args.height, args.fps)
