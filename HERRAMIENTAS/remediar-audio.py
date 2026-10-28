#!/usr/bin/env python3
"""
Script de Remediacion y Normalizacion de Audio (2-Pass EBU R128 / loudnorm)
Corrige el True Peak y la sonoridad integrada a los estandares de emision (-14 LUFS, -1.0 dBTP).
"""

import os
import sys
import json
import subprocess
import argparse
import re

def analyze_loudness(path):
    """Devuelve las estadisticas de loudnorm o None si no se pueden medir."""
    cmd = [
        "ffmpeg", "-nostats", "-i", path,
        "-af", "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json",
        "-f", "null", "-"
    ]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, errors="replace")
    match = re.search(r"\{[\s\S]*\"input_i\"[\s\S]*\}", res.stderr)
    if not match:
        return None
    return json.loads(match.group(0))


def remediate_file(input_file, output_file=None):
    if not os.path.exists(input_file):
        print(f"[!] Archivo no encontrado: {input_file}")
        return False

    if not output_file:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_master_ebur128{ext}"

    print(f"[*] Remediando audio en: {os.path.basename(input_file)}")
    print("    Pase 1: Analizando estadisticas lineales...")

    # Pase 1: Análisis loudnorm
    stats = analyze_loudness(input_file)
    if not stats:
        print("[!] Error: No se pudo obtener el reporte de loudnorm en el pase 1.")
        return False

    print(f"    Medido actual: I={stats['input_i']} LUFS, TP={stats['input_tp']} dBTP, LRA={stats['input_lra']}")

    # Pase 2: Renderizado con normalización exacta y limitador para prevenir inter-sample peaks en AAC
    print("    Pase 2: Aplicando ecualizacion y limitacion dinamica...")
    af_filter = (
        f"loudnorm=I=-14:TP=-2.0:LRA=11:"
        f"measured_I={stats['input_i']}:"
        f"measured_TP={stats['input_tp']}:"
        f"measured_LRA={stats['input_lra']}:"
        f"measured_thresh={stats['input_thresh']}:"
        f"offset={stats['target_offset']}:linear=true,"
        f"alimiter=limit=-2.0dB:level=false"
    )

    cmd_pass2 = [
        "ffmpeg", "-y", "-i", input_file,
        "-c:v", "copy",
        "-af", af_filter,
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        output_file
    ]
    res2 = subprocess.run(cmd_pass2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
    if res2.returncode != 0:
        print(f"[!] Error al exportar archivo remediado: {res2.stderr}")
        return False

    # Verificar el resultado real. No basta con que FFmpeg escriba un archivo:
    # el master debe quedar dentro del rango EBU R128 del Quality Gate.
    final_stats = analyze_loudness(output_file)
    if not final_stats:
        print("[!] Error: No se pudo verificar la sonoridad del archivo remediado.")
        return False
    try:
        final_i = float(final_stats["input_i"])
        final_tp = float(final_stats["input_tp"])
    except (KeyError, TypeError, ValueError):
        print(f"[!] Error: Reporte de sonoridad invalido: {final_stats}")
        return False

    print(f"    Resultado: I={final_i:.1f} LUFS, TP={final_tp:.1f} dBTP")
    if final_i < -16.0 or final_i > -13.0:
        print(
            f"[!] El master no alcanzo el rango EBU R128 [-16.0, -13.0] LUFS "
            f"(quedo en {final_i:.1f} LUFS)."
        )
        return False
    if final_tp > -1.0:
        print(f"[!] El master supera el True Peak maximo de -1.0 dBTP ({final_tp:.1f}).")
        return False

    print(f"[OK] Archivo remediado y verificado: {output_file}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remediador de Audio EBU R128 (-14 LUFS / -1 dBTP)")
    parser.add_argument("input_file", help="Ruta al video o audio a normalizar")
    parser.add_argument("--out", "-o", help="Ruta de salida (por defecto: nombre_master_ebur128.mp4)")
    args = parser.parse_args()

    ok = remediate_file(args.input_file, args.out)
    if not ok:
        print("[ERROR] No se pudo remediar el audio.", file=sys.stderr)
        sys.exit(1)
