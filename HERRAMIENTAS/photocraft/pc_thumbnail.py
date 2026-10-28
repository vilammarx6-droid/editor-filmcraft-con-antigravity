#!/usr/bin/env python3
"""
pc_thumbnail.py - Generador de Miniaturas y Portadas con PhotoCraft CLI
Crea miniaturas de alta conversión para YouTube/Shorts/TikTok combinando:
1. Fotograma clave del video o preview QA
2. Tipografías de alto impacto (Anton, Bebas Neue, Montserrat)
3. Procesamiento y optimización determinista con PhotoCraft CLI
4. Emisión de manifiesto criptográfico SHA-256 (thumbnail-manifest.json)
"""

import os
import sys
import json
import hashlib
import argparse
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

def get_photocraft_cli():
    # 1. Variable de entorno (prioridad si está configurada)
    cli = os.environ.get("PHOTOCRAFT_CLI")
    if cli:
        return cli
    
    # 2. Config local
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(script_dir, "..", "config.local.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                cand = cfg.get("photocraft_cli")
                if cand and os.path.exists(cand):
                    return cand
        except Exception:
            pass

    # 3. Rutas por defecto
    user_home = os.environ.get("USERPROFILE", "")
    cand = os.path.join(user_home, ".gemini", "antigravity", "scratch", "craft_tools", "photocraft", "photocraft-0.16.0-windows-x64-portable", "photocraft-cli.exe")
    if os.path.exists(cand):
        return cand
    
    return "photocraft-cli.exe"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def find_font(repo_root, font_name="Anton-Regular.ttf"):
    fonts_dir = os.path.join(repo_root, "RECURSOS_COMPARTIDOS", "04_licencias_y_fuentes")
    font_path = os.path.join(fonts_dir, font_name)
    if os.path.exists(font_path):
        return font_path
    
    # Búsqueda recursiva
    for root, _, files in os.walk(fonts_dir):
        if font_name in files:
            return os.path.join(root, font_name)
    return None

def create_thumbnail(project_dir, title=None, subtitle=None, hero_image=None, aspect="16:9", output_file=None, allow_fallback=False, allow_blank=False):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    project_dir = os.path.abspath(project_dir)

    if not os.path.isdir(project_dir):
        raise RuntimeError(f"El proyecto no existe o no es una carpeta: {project_dir}")

    # Definir dimensiones según aspecto
    if aspect == "9:16":
        width, height = 1080, 1920
    elif aspect == "1:1":
        width, height = 1080, 1080
    else: # 16:9
        width, height = 1920, 1080

    # Localizar imagen base si no se especifica
    if not hero_image or not os.path.exists(hero_image):
        previews_dir = os.path.join(project_dir, "04_previews")
        candidates = [
            os.path.join(previews_dir, "qa_01_frame.png"),
            os.path.join(previews_dir, "collage_qc.png"),
        ]
        for c in candidates:
            if os.path.exists(c):
                hero_image = c
                break

    if not hero_image or not os.path.exists(hero_image):
        if not allow_blank:
            raise RuntimeError(
                "No se encontro imagen hero para la miniatura. "
                "Genere 04_previews/qa_01_frame.png o pase --hero; "
                "use --allow-blank solo si una portada vacia es intencional."
            )
        print(f"[!] No se encontro imagen hero para el proyecto: {project_dir}")
        base_img = Image.new("RGB", (width, height), color=(20, 24, 33))
    else:
        print(f"[*] Usando imagen base: {os.path.basename(hero_image)}")
        base_img = Image.open(hero_image).convert("RGB")
        # Redimensionar cubriendo el lienzo (cover)
        img_ratio = base_img.width / base_img.height
        target_ratio = width / height
        if img_ratio > target_ratio:
            new_h = height
            new_w = int(height * img_ratio)
        else:
            new_w = width
            new_h = int(width / img_ratio)
        base_img = base_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        # Recorte centrado
        left = (new_w - width) // 2
        top = (new_h - height) // 2
        base_img = base_img.crop((left, top, left + width, top + height))

    # Mejorar contraste y saturación para impacto visual de miniatura
    enhancer_con = ImageEnhance.Contrast(base_img)
    base_img = enhancer_con.enhance(1.15)
    enhancer_col = ImageEnhance.Color(base_img)
    base_img = enhancer_col.enhance(1.20)

    # Añadir viñeta degradada inferior para legibilidad del texto
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    
    grad_height = int(height * 0.55)
    for y in range(grad_height):
        alpha = int((y / grad_height) ** 1.8 * 230)
        draw_ov.line([(0, height - grad_height + y), (width, height - grad_height + y)], fill=(10, 12, 18, alpha))
    
    base_img = Image.alpha_composite(base_img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(base_img)

    # Tipografía
    font_file = find_font(repo_root, "Anton-Regular.ttf") or find_font(repo_root, "BebasNeue-Regular.ttf")
    
    if not title:
        # Intentar extraer título del brief.md
        brief_file = os.path.join(project_dir, "00_brief", "brief.md")
        if os.path.exists(brief_file):
            with open(brief_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("# ") or "Título:" in line or "Titulo:" in line:
                        title = line.replace("#", "").replace("Título:", "").replace("Titulo:", "").strip()
                        break
        if not title:
            title = os.path.basename(project_dir).replace("_", " ").title()

    title_text = title.upper()
    font_size = int(height * 0.11)
    
    try:
        font = ImageFont.truetype(font_file, font_size) if font_file else ImageFont.load_default()
        sub_font = ImageFont.truetype(font_file, int(font_size * 0.55)) if font_file else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    # Dibujar texto con borde / sombra de impacto
    margin_x = int(width * 0.08)
    pos_y = int(height * 0.70)
    
    # Borde negro grueso
    stroke_w = max(4, int(font_size * 0.06))
    draw.text((margin_x, pos_y), title_text, font=font, fill=(255, 221, 51), stroke_width=stroke_w, stroke_fill=(0, 0, 0))
    
    if subtitle:
        sub_y = pos_y + int(font_size * 1.1)
        draw.text((margin_x, sub_y), subtitle.upper(), font=sub_font, fill=(255, 255, 255), stroke_width=stroke_w // 2, stroke_fill=(0, 0, 0))

    # Guardar imagen temporal con ruta absoluta
    if not output_file:
        exports_dir = os.path.join(project_dir, "03_exports")
        os.makedirs(exports_dir, exist_ok=True)
        output_file = os.path.join(exports_dir, "thumbnail.jpg")

    output_file = os.path.abspath(output_file)
    temp_png = os.path.abspath(output_file + ".raw.png")
    base_img.convert("RGB").save(temp_png, "PNG")

    # Optimizar y convertir con PhotoCraft CLI
    pc_cli = get_photocraft_cli()
    print(f"[*] Procesando y optimizando con PhotoCraft CLI: {pc_cli}")
    
    cmd = [pc_cli, "convert", temp_png, output_file, "--quality", "92"]
    ret_code = 0
    err_msg = ""
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        ret_code = res.returncode
        err_msg = res.stderr.strip() or res.stdout.strip()
    except Exception as e:
        ret_code = -1
        err_msg = str(e)
    
    if os.path.exists(temp_png):
        try:
            os.remove(temp_png)
        except Exception:
            pass

    engine_used = "PhotoCraft CLI 0.16.0"
    status_str = "ok"
    warning_msg = None

    if ret_code != 0 or not os.path.exists(output_file):
        if not err_msg:
            err_msg = "Archivo de salida no generado"
        if not allow_fallback:
            raise RuntimeError(f"Fallo critico en PhotoCraft CLI (exit code {ret_code}): {err_msg}")
        
        # Fallback a guardado directo degradado con PIL si se solicito explicitamente
        print(f"[!] Aviso: PhotoCraft CLI fallo ({err_msg}). Guardando con PIL en modo degradado...")
        base_img.convert("RGB").save(output_file, "JPEG", quality=92)
        engine_used = "PIL"
        status_str = "degradado"
        warning_msg = f"PhotoCraft CLI fallo ({err_msg}). Salida generada mediante fallback PIL."

    # Validar dimensiones reales con PhotoCraft CLI info. No se acepta una
    # salida cuyo tamaño no pueda verificarse.
    try:
        info_res = subprocess.run([pc_cli, "info", output_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        doc_info = json.loads(info_res.stdout) if info_res.returncode == 0 else {}
    except Exception:
        doc_info = {}

    if status_str == "ok":
        info_w = int(doc_info.get("width", 0) or 0)
        info_h = int(doc_info.get("height", 0) or 0)
        if info_w != width or info_h != height:
            raise RuntimeError(
                "PhotoCraft no pudo verificar la salida: "
                f"esperado {width}x{height}, info devolvio {info_w}x{info_h}."
            )

    sha256_hash = sha256_file(output_file)
    file_size = os.path.getsize(output_file)

    manifest = {
        "status": status_str,
        "engine": engine_used,
        "thumbnail_file": os.path.basename(output_file),
        "output_path": output_file,
        "width": doc_info.get("width", width),
        "height": doc_info.get("height", height),
        "aspect": aspect,
        "size_bytes": file_size,
        "sha256": sha256_hash
    }
    if hero_image and os.path.exists(hero_image):
        manifest["source_image"] = os.path.basename(hero_image)
        manifest["source_sha256"] = sha256_file(hero_image)
    else:
        manifest["source_image"] = None
        manifest["source_sha256"] = None
    if warning_msg:
        manifest["warning"] = warning_msg
    if not hero_image:
        manifest["warning"] = "Miniatura generada sin imagen hero (--allow-blank)."

    manifest_path = os.path.join(os.path.dirname(output_file), "thumbnail-manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[{'OK' if status_str == 'ok' else 'AVISO'}] Miniatura emitida ({engine_used}): {output_file} ({width}x{height})")
    print(f"     Status:    {status_str}")
    print(f"     SHA-256:   {sha256_hash}")
    print(f"     Manifest:  {manifest_path}")
    return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de Miniaturas con PhotoCraft")
    parser.add_argument("--project", required=True, help="Ruta al proyecto")
    parser.add_argument("--title", help="Titulo principal para la miniatura")
    parser.add_argument("--subtitle", help="Subtitulo secundario")
    parser.add_argument("--aspect", default="16:9", choices=["16:9", "9:16", "1:1"], help="Aspect ratio")
    parser.add_argument("--hero", help="Ruta a imagen base de partida")
    parser.add_argument("--out", help="Ruta de salida")
    parser.add_argument("--allow-fallback", action="store_true", help="Permitir fallback degradado con PIL si falla PhotoCraft")
    parser.add_argument("--allow-blank", action="store_true", help="Permitir portada sin imagen hero (solo si es intencional)")
    
    args = parser.parse_args()
    try:
        manifest = create_thumbnail(
            args.project,
            args.title,
            args.subtitle,
            args.hero,
            args.aspect,
            args.out,
            allow_fallback=args.allow_fallback,
            allow_blank=args.allow_blank,
        )
        if manifest.get("status") == "degradado" and not args.allow_fallback:
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
