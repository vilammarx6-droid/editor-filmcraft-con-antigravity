import os
import math
from PIL import Image, ImageDraw, ImageFilter

OUTPUT_DIR = r"C:\Users\marx_\OneDrive\Documentos\Proyecto predeterminado\EditorVideo\RECURSOS_COMPARTIDOS\03_animaciones_y_graficos"

def gen_circulo():
    size = (800, 800)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Draw glowing hand-drawn marker circle (neon red/yellow)
    bbox = [100, 100, 700, 700]
    draw.ellipse(bbox, outline=(255, 50, 50, 240), width=28)
    # Add a second overlapping arc for organic hand-drawn look
    draw.arc([90, 85, 710, 715], start=45, end=330, fill=(255, 90, 50, 220), width=20)
    img.save(os.path.join(OUTPUT_DIR, "circulo_resaltador.png"), "PNG")
    print("Generated: circulo_resaltador.png")

def gen_flecha():
    size = (800, 800)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Bold bright yellow arrow pointing down-right
    points = [
        (150, 300), (450, 300), (450, 180),
        (700, 400), (450, 620), (450, 500), (150, 500)
    ]
    # Black outline for contrast on any video background
    draw.polygon(points, fill=(255, 220, 0, 255), outline=(10, 10, 10, 255), width=18)
    img.save(os.path.join(OUTPUT_DIR, "flecha_amarilla.png"), "PNG")
    print("Generated: flecha_amarilla.png")

def gen_check():
    size = (512, 512)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Green circle
    draw.ellipse([40, 40, 472, 472], fill=(46, 204, 113, 255), outline=(255, 255, 255, 240), width=16)
    # White checkmark
    check_pts = [(130, 260), (220, 360), (380, 160)]
    draw.line(check_pts, fill=(255, 255, 255, 255), width=36, joint="curve")
    img.save(os.path.join(OUTPUT_DIR, "icono_check_verde.png"), "PNG")
    print("Generated: icono_check_verde.png")

def gen_alerta():
    size = (512, 512)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Triangle
    tri = [(256, 40), (472, 450), (40, 450)]
    draw.polygon(tri, fill=(241, 196, 15, 255), outline=(20, 20, 20, 255), width=18)
    # Exclamation mark
    draw.line([(256, 170), (256, 320)], fill=(20, 20, 20, 255), width=28)
    draw.ellipse([242, 365, 270, 393], fill=(20, 20, 20, 255))
    img.save(os.path.join(OUTPUT_DIR, "icono_alerta_amarillo.png"), "PNG")
    print("Generated: icono_alerta_amarillo.png")

def gen_vignette(w, h, filename):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Radial falloff
    cx, cy = w / 2.0, h / 2.0
    max_r = math.sqrt(cx**2 + cy**2)
    
    # We can create a low-res vignette and resize with bilinear for super smooth gradient
    rw, rh = w // 4, h // 4
    v_small = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    rcx, rcy = rw / 2.0, rh / 2.0
    rmax = math.sqrt(rcx**2 + rcy**2)
    
    pixels = v_small.load()
    for y in range(rh):
        for x in range(rw):
            dist = math.sqrt((x - rcx)**2 + (y - rcy)**2)
            ratio = dist / rmax
            # Transparent inside (up to 45%), dark outside
            if ratio < 0.45:
                alpha = 0
            else:
                norm = (ratio - 0.45) / 0.55
                alpha = int(min(200, (norm ** 1.8) * 200))
            pixels[x, y] = (0, 0, 0, alpha)
            
    v_large = v_small.resize((w, h), Image.Resampling.BICUBIC)
    v_large.save(os.path.join(OUTPUT_DIR, filename), "PNG")
    print(f"Generated: {filename} ({w}x{h})")

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    gen_circulo()
    gen_flecha()
    gen_check()
    gen_alerta()
    gen_vignette(720, 1280, "vineta_cinematica_vertical_720.png")
    gen_vignette(1280, 720, "vineta_cinematica_horizontal_720.png")
    print("All graphic assets generated successfully!")
