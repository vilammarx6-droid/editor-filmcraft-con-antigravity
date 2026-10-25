#!/usr/bin/env python3
"""
Constructor del template limpio 'lower-third' para EffectCraft.
1. Crea proyecto desde 'lower-third' via templates.create.
2. Elimina la capa 'Preview Background (delete over footage)' via script --eval.
3. Exporta la composición limpia a .ectemplate via essential.exportTemplate.
4. Verifica controles, resolución, fps y duración via essential.templateInfo.
"""

import os
import sys
import json
import subprocess

def get_effectcraft_cli():
    # 1. Variable de entorno
    if os.environ.get("EFFECTCRAFT_CLI") and os.path.exists(os.environ["EFFECTCRAFT_CLI"]):
        return os.environ["EFFECTCRAFT_CLI"]

    # 2. config.local.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.abspath(os.path.join(script_dir, "..", "config.local.json"))
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8-sig") as f:
            cfg = json.load(f)
            if cfg.get("effectcraft_cli") and os.path.exists(cfg["effectcraft_cli"]):
                return cfg["effectcraft_cli"]

    # 3. Fallback
    cand = os.path.expanduser(r"~/.gemini/antigravity/scratch/craft_tools/effectcraft/effectcraft-0.11.1-windows-x64-portable/effectcraft-cli.exe")
    if os.path.exists(cand):
        return cand
        
    raise FileNotFoundError("No se encontró effectcraft-cli.exe. Ejecuta setup-entorno.ps1")

def build_clean_template():
    cli = get_effectcraft_cli()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(script_dir, "templates")
    os.makedirs(templates_dir, exist_ok=True)

    temp_proj = os.path.join(templates_dir, "_temp_lower_third.ecproj")
    template_out = os.path.join(templates_dir, "lower_third_clean.ectemplate")

    print("[*] Paso 1: Creando proyecto temporal desde template 'lower-third'...")
    cmd1 = [cli, "exec", "templates.create", "--params", json.dumps({"id": "lower-third", "projectPath": temp_proj})]
    res1 = subprocess.run(cmd1, capture_output=True, text=True)
    if res1.returncode != 0:
        raise RuntimeError(f"Error en templates.create: {res1.stderr}")

    print("[*] Paso 2: Eliminando capa 'Preview Background (delete over footage)' via script --eval...")
    js_code = """
    var comp = app.project.activeItem;
    var layer = comp.layer("Preview Background (delete over footage)");
    if (layer) {
        layer.remove();
        writeLn("OK_REMOVED");
    } else {
        writeLn("LAYER_NOT_FOUND");
    }
    """
    cmd2 = [cli, "--project", temp_proj, "--save", "script", "--eval", js_code]
    res2 = subprocess.run(cmd2, capture_output=True, text=True)
    if "OK_REMOVED" not in res2.stdout:
        print(f"[!] Advertencia en script eval: {res2.stdout} {res2.stderr}")

    print("[*] Paso 3: Exportando composicion limpia a .ectemplate via essential.exportTemplate...")
    cmd3 = [cli, "--project", temp_proj, "exec", "essential.exportTemplate", "--params", json.dumps({"path": template_out})]
    res3 = subprocess.run(cmd3, capture_output=True, text=True)
    if res3.returncode != 0:
        raise RuntimeError(f"Error en essential.exportTemplate: {res3.stderr}")

    print("[*] Paso 4: Verificando controles, resolucion, fps y duracion via essential.templateInfo...")
    cmd4 = [cli, "exec", "essential.templateInfo", "--params", json.dumps({"path": template_out})]
    res4 = subprocess.run(cmd4, capture_output=True, text=True)
    if res4.returncode != 0:
        raise RuntimeError(f"Error en essential.templateInfo: {res4.stderr}")

    info = json.loads(res4.stdout)
    controls = [c["name"] for c in info.get("controls", [])]
    w = info.get("width")
    h = info.get("height")
    fps = info.get("frameRate")
    dur = info.get("duration")

    print(f"\n[OK] Template generado exitosamente: {template_out}")
    print(f"     Composicion: {info.get('compName')}")
    print(f"     Resolucion:  {w}x{h}")
    print(f"     Framerate:   {fps} fps")
    print(f"     Duracion:    {dur} s")
    print(f"     Controles:   {', '.join(controls)}")

    # Limpiar proyecto temporal
    if os.path.exists(temp_proj):
        try: os.remove(temp_proj)
        except Exception: pass

    return template_out, info

if __name__ == "__main__":
    build_clean_template()
