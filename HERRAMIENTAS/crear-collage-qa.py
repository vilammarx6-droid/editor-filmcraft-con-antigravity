import os
import sys
import argparse
from PIL import Image, ImageDraw

def resolve_project_path(raw_path):
    # Resolver ruta relativa o nombre de proyecto
    if os.path.exists(raw_path):
        return os.path.abspath(raw_path)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, ".."))
    
    cand1 = os.path.join(repo_root, raw_path)
    if os.path.exists(cand1):
        return cand1
        
    cand2 = os.path.join(repo_root, "PROYECTOS", raw_path)
    if os.path.exists(cand2):
        return cand2
        
    # Búsqueda parcial en PROYECTOS
    proyectos_dir = os.path.join(repo_root, "PROYECTOS")
    if os.path.exists(proyectos_dir):
        for d in os.listdir(proyectos_dir):
            if raw_path.lower() in d.lower() and os.path.isdir(os.path.join(proyectos_dir, d)):
                return os.path.join(proyectos_dir, d)
                
    raise FileNotFoundError(f"No se encontró el proyecto: {raw_path}")

def select_qa_frames(previews_dir, explicit_frames=None):
    if explicit_frames:
        resolved = []
        for f in explicit_frames:
            p = f if os.path.isabs(f) else os.path.join(previews_dir, f)
            if os.path.exists(p):
                resolved.append(p)
            else:
                print(f"[!] Advertencia: Fotograma especificado no existe: {p}")
        if resolved:
            return resolved

    # 1. Buscar fotogramas con convención de nombres determinista (qa_01*, qa_02*, etc.)
    all_files = os.listdir(previews_dir)
    qa_convention = [os.path.join(previews_dir, f) for f in all_files 
                     if f.lower().startswith("qa_") and f.lower().endswith((".png", ".jpg", ".jpeg"))]
    if qa_convention:
        qa_convention.sort()
        return qa_convention[:4]

    # 2. Filtrar fotogramas válidos ignorando archivos temporales o de depuración
    ignore_prefixes = ("collage_", "test_", "check_", "trans_", "finalcheck_", "tmp_")
    valid_candidates = []
    for f in all_files:
        lower = f.lower()
        if lower.endswith((".png", ".jpg", ".jpeg")) and not any(lower.startswith(p) for p in ignore_prefixes):
            valid_candidates.append(os.path.join(previews_dir, f))

    # Ordenar por fecha de modificación
    valid_candidates.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    selected = valid_candidates[:4]
    selected.reverse()
    return selected

def make_collage(project_arg, explicit_frames=None):
    project_path = resolve_project_path(project_arg)
    previews_dir = os.path.join(project_path, "04_previews")
    if not os.path.exists(previews_dir):
        print(f"No existe la carpeta de previews: {previews_dir}")
        return None

    selected = select_qa_frames(previews_dir, explicit_frames)

    if not selected:
        print("No se encontraron capturas válidas en 04_previews.")
        return None

    print(f"Generando collage QA con {len(selected)} fotogramas:")
    for idx, s in enumerate(selected):
        print(f"  [{idx + 1}] {os.path.basename(s)}")

    imgs = [Image.open(p).convert("RGB") for p in selected]
    n = len(imgs)

    # Dimensiones estándar para la miniatura
    if imgs[0].width >= imgs[0].height:
        thumb_w, thumb_h = 480, 270
    else:
        thumb_w, thumb_h = 270, 480
    
    if n == 1:
        grid_w, grid_h = thumb_w, thumb_h
        cols, rows = 1, 1
    elif n == 2:
        grid_w, grid_h = thumb_w * 2, thumb_h
        cols, rows = 2, 1
    else:
        grid_w, grid_h = thumb_w * 2, thumb_h * 2
        cols, rows = 2, 2

    collage = Image.new("RGB", (grid_w, grid_h), (20, 24, 33))
    draw = ImageDraw.Draw(collage)

    for idx, img in enumerate(imgs):
        resized = img.resize((thumb_w, thumb_h), Image.Resampling.BILINEAR)
        c = idx % cols
        r = idx // cols
        x = c * thumb_w
        y = r * thumb_h
        collage.paste(resized, (x, y))
        # Etiqueta de número de toma / nombre
        base_name = os.path.splitext(os.path.basename(selected[idx]))[0]
        label = f"{idx + 1}. {base_name[:18]}"
        draw.rectangle([x + 8, y + 8, x + 160, y + 32], fill=(10, 15, 25))
        draw.text((x + 14, y + 12), label, fill=(0, 230, 153))

    out_path = os.path.join(previews_dir, "collage_qc.png")
    collage.save(out_path, "PNG", optimize=True)
    print(f"[OK] Collage QA generado: {out_path} ({grid_w}x{grid_h})")
    return out_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador determinista de collage QA")
    parser.add_argument("proyecto", help="Nombre o ruta del proyecto")
    parser.add_argument("--frames", nargs="*", help="Lista explícita de fotogramas a incluir")
    args = parser.parse_args()

    result = make_collage(args.proyecto, args.frames)
    if not result:
        sys.exit(1)
