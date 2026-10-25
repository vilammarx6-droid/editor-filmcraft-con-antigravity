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
    cmd_pass1 = [
        "ffmpeg", "-nostats", "-i", input_file,
        "-af", "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json",
        "-f", "null", "-"
    ]
    res1 = subprocess.run(cmd_pass1, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, errors="replace")
    
    # Extraer JSON de salida de loudnorm
    match = re.search(r"\{[\s\S]*\"input_i\"[\s\S]*\}", res1.stderr)
    if not match:
        print("[!] Error: No se pudo obtener el reporte de loudnorm en el pase 1.")
        return False

    stats = json.loads(match.group(0))
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
        "-c:a", "aac", "-b:a", "192k",
        output_file
    ]
    res2 = subprocess.run(cmd_pass2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
    if res2.returncode != 0:
        print(f"[!] Error al exportar archivo remediado: {res2.stderr}")
        return False

    print(f"[OK] Archivo remediado con exito: {output_file}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remediador de Audio EBU R128 (-14 LUFS / -1 dBTP)")
    parser.add_argument("input_file", help="Ruta al video o audio a normalizar")
    parser.add_argument("--out", "-o", help="Ruta de salida (por defecto: nombre_master_ebur128.mp4)")
    args = parser.parse_args()

    remediate_file(args.input_file, args.out)
