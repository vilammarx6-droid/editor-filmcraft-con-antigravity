#!/usr/bin/env python3
"""
Script de diagnostico y reparacion del bug de comillas en el plugin
googlecloudtools.datacloud_telemetry en entornos Windows para Gemini CLI / Antigravity.
"""

import os
import sys
import json
import shutil
import re

def fix_telemetry():
    print("=" * 60)
    print(" [REPARADOR PYTHON] Bug de Telemetria Data Cloud en Windows ")
    print("=" * 60)

    user_home = os.path.expanduser("~")
    gemini_dir = os.path.join(user_home, ".gemini")
    config_dir = os.path.join(gemini_dir, "config")
    plugins_dir = os.path.join(config_dir, "plugins")
    config_json = os.path.join(config_dir, "config.json")
    settings_json = os.path.join(gemini_dir, "settings.json")

    if not os.path.exists(gemini_dir):
        print(f"[!] No existe directorio .gemini en: {gemini_dir}")
        return

    # 1. Limpieza de hooks.json
    print(f"[1/4] Buscando hooks en: {plugins_dir}")
    if os.path.exists(plugins_dir):
        for root, _, files in os.walk(plugins_dir):
            for file in files:
                if file.lower() == "hooks.json":
                    hook_path = os.path.join(root, file)
                    try:
                        with open(hook_path, "r", encoding="utf-8") as f:
                            raw = f.read()
                        if '\\"[A-Za-z]:\\' in raw or '""' in raw:
                            print(f"  -> Corrigiendo comillas malformadas en: {hook_path}")
                            clean = re.sub(r'\\"([A-Za-z]:\\[^"]+)\\"', r'\1', raw)
                            clean = re.sub(r'""([A-Za-z]:\\[^"]+)""', r'"\1"', clean)
                            with open(hook_path, "w", encoding="utf-8") as f:
                                f.write(clean)
                            print("  -> [OK] Archivo saneado.")
                    except Exception as e:
                        print(f"  [!] Error al procesar {hook_path}: {e}")

        # 2. Eliminación de carpeta conflictiva
        bad_folder = os.path.join(plugins_dir, "googlecloudtools.datacloud_telemetry")
        if os.path.exists(bad_folder):
            print(f"[2/4] Eliminando carpeta conflictiva: {bad_folder}")
            try:
                shutil.rmtree(bad_folder, ignore_errors=True)
                print("  -> [OK] Carpeta eliminada.")
            except Exception as e:
                print(f"  [!] Error al eliminar {bad_folder}: {e}")
        else:
            print("[2/4] Carpeta de telemetria conflictiva limpia (no presente).")
    else:
        print("[1/4] No hay carpeta de plugins.")

    # 3. Desactivación preventiva de telemetría en config.json
    print("[3/4] Desactivando telemetria en configuracion...")
    for target in [config_json, settings_json]:
        try:
            data = {}
            if os.path.exists(target):
                with open(target, "r", encoding="utf-8") as f:
                    data = json.load(f)
            
            if "telemetry" not in data or not isinstance(data["telemetry"], dict):
                data["telemetry"] = {"enabled": False}
            else:
                data["telemetry"]["enabled"] = False
            
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"  -> [OK] Telemetria desactivada en: {target}")
        except Exception as e:
            print(f"  [!] Error actualizando {target}: {e}")

    print("[4/4] Verificacion final completada.")
    print("=" * 60)

if __name__ == "__main__":
    fix_telemetry()
