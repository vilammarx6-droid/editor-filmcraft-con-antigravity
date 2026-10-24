import os
import sys
from PIL import Image, ImageDraw, ImageFont

def make_collage(project_path):
    previews_dir = os.path.join(project_path, "04_previews")
    if not os.path.exists(previews_dir):
        print(f"No existe la carpeta de previews: {previews_dir}")
        return None

    # Buscar imágenes PNG (excluyendo collages previos)
    files = [os.path.join(previews_dir, f) for f in os.listdir(previews_dir)
             if f.lower().endswith(".png") and not f.startswith("collage_")]
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    if not files:
        print("No se encontraron capturas en 04_previews.")
        return None

    # Tomar hasta 4 capturas más recientes
    selected = files[:4]
    selected.reverse()  # Orden cronológico

    imgs = [Image.open(p).convert("RGB") for p in selected]
    n = len(imgs)

    # Dimensiones estándar para la miniatura
    if imgs[0].width > imgs[0].height:
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

    collage = Image.new("RGB", (grid_w, grid_h), (25, 25, 25))
    draw = ImageDraw.Draw(collage)

    for idx, img in enumerate(imgs):
        resized = img.resize((thumb_w, thumb_h), Image.Resampling.BILINEAR)
        c = idx % cols
        r = idx // cols
        x = c * thumb_w
        y = r * thumb_h
        collage.paste(resized, (x, y))
        # Etiqueta de número de toma
        draw.rectangle([x + 10, y + 10, x + 90, y + 36], fill=(0, 0, 0))
        draw.text((x + 16, y + 14), f"Toma {idx + 1}", fill=(255, 255, 255))

    out_path = os.path.join(previews_dir, "collage_qc.png")
    collage.save(out_path, "PNG", optimize=True)
    print(f"Collage QA generado exitosamente: {out_path} ({grid_w}x{grid_h})")
    return out_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python crear-collage-qa.py <ruta_proyecto>")
        sys.exit(1)
    make_collage(sys.argv[1])
