import os
import math
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = r"C:\Users\marx_\OneDrive\Documentos\Proyecto predeterminado\EditorVideo\RECURSOS_COMPARTIDOS\03_animaciones_y_graficos"
STICKERS_DIR = os.path.join(BASE_DIR, "stickers_y_memes")
MARCOS_DIR = os.path.join(BASE_DIR, "marcos_y_camaras")

os.makedirs(STICKERS_DIR, exist_ok=True)
os.makedirs(MARCOS_DIR, exist_ok=True)

# 1. Pixelated Thug Life Sunglasses (800x260)
def gen_thug_life():
    w, h = 800, 260
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 8-bit pixel block grid
    bs = 20  # block size
    # Left lens, right lens, bridge, and side arms
    # Draw pixelated glasses
    # Left arm:
    for x in range(2, 8): draw.rectangle([x*bs, 3*bs, (x+1)*bs, 4*bs], fill=(15, 15, 15, 255))
    # Right arm:
    for x in range(32, 38): draw.rectangle([x*bs, 3*bs, (x+1)*bs, 4*bs], fill=(15, 15, 15, 255))
    # Left lens body:
    for y in range(4, 9):
        for x in range(6, 18):
            draw.rectangle([x*bs, y*bs, (x+1)*bs, (y+1)*bs], fill=(15, 15, 15, 255))
    # Right lens body:
    for y in range(4, 9):
        for x in range(22, 34):
            draw.rectangle([x*bs, y*bs, (x+1)*bs, (y+1)*bs], fill=(15, 15, 15, 255))
    # Bridge:
    for x in range(18, 22):
        draw.rectangle([x*bs, 4*bs, (x+1)*bs, 5*bs], fill=(15, 15, 15, 255))
    # White reflection pixels (classic 8-bit glare)
    draw.rectangle([7*bs, 5*bs, 8*bs, 6*bs], fill=(255, 255, 255, 255))
    draw.rectangle([8*bs, 6*bs, 9*bs, 7*bs], fill=(255, 255, 255, 255))
    draw.rectangle([23*bs, 5*bs, 24*bs, 6*bs], fill=(255, 255, 255, 255))
    draw.rectangle([24*bs, 6*bs, 25*bs, 7*bs], fill=(255, 255, 255, 255))
    
    img.save(os.path.join(STICKERS_DIR, "lentes_thug_life_meme.png"), "PNG")
    print("Created: lentes_thug_life_meme.png")

# 2. Comic Speech Bubble (800x600)
def gen_comic_bubble():
    w, h = 800, 600
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # White rounded rectangle with black border
    bbox = [40, 40, 760, 440]
    draw.rounded_rectangle(bbox, radius=60, fill=(255, 255, 255, 255), outline=(15, 15, 15, 255), width=18)
    # Speech tail pointing bottom-left
    tail = [(140, 435), (80, 560), (240, 435)]
    draw.polygon(tail, fill=(255, 255, 255, 255), outline=(15, 15, 15, 255))
    # Overwrite seam with white
    draw.line([(145, 435), (235, 435)], fill=(255, 255, 255, 255), width=20)
    img.save(os.path.join(STICKERS_DIR, "bocadillo_dialogo_comic.png"), "PNG")
    print("Created: bocadillo_dialogo_comic.png")

# 3. Comic Thought Bubble (800x600)
def gen_thought_bubble():
    w, h = 800, 600
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Cloud circles
    circles = [
        (400, 240, 180), (260, 260, 140), (540, 260, 140),
        (320, 160, 130), (480, 160, 130), (210, 320, 100),
        (590, 320, 100), (400, 340, 130)
    ]
    # Draw black outline circles
    for cx, cy, r in circles:
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(15, 15, 15, 255), width=16)
    # Fill with white
    for cx, cy, r in circles:
        draw.ellipse([cx-r+8, cy-r+8, cx+r-8, cy+r-8], fill=(255, 255, 255, 255))
    # Little trailing cloud dots
    draw.ellipse([180, 460, 240, 520], fill=(255, 255, 255, 255), outline=(15, 15, 15, 255), width=14)
    draw.ellipse([130, 530, 170, 570], fill=(255, 255, 255, 255), outline=(15, 15, 15, 255), width=12)
    img.save(os.path.join(STICKERS_DIR, "bocadillo_pensamiento_cloud.png"), "PNG")
    print("Created: bocadillo_pensamiento_cloud.png")

# 4. Viewfinder Camera REC Overlay (720x1280 Vertical)
def gen_viewfinder_vertical():
    w, h = 720, 1280
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Corner brackets (Top-left, top-right, bottom-left, bottom-right)
    m = 50  # margin
    arm = 60
    lw = 6  # line width
    white = (255, 255, 255, 230)
    
    # Top-Left
    draw.line([(m, m), (m + arm, m)], fill=white, width=lw)
    draw.line([(m, m), (m, m + arm)], fill=white, width=lw)
    # Top-Right
    draw.line([(w - m - arm, m), (w - m, m)], fill=white, width=lw)
    draw.line([(w - m, m), (w - m, m + arm)], fill=white, width=lw)
    # Bottom-Left
    draw.line([(m, h - m), (m + arm, h - m)], fill=white, width=lw)
    draw.line([(m, h - m - arm), (m, h - m)], fill=white, width=lw)
    # Bottom-Right
    draw.line([(w - m - arm, h - m), (w - m, h - m)], fill=white, width=lw)
    draw.line([(w - m, h - m - arm), (w - m, h - m)], fill=white, width=lw)
    
    # Center crosshair (+)
    cx, cy = w // 2, h // 2
    c_len = 24
    draw.line([(cx - c_len, cy), (cx + c_len, cy)], fill=(255, 255, 255, 180), width=3)
    draw.line([(cx, cy - c_len), (cx, cy + c_len)], fill=(255, 255, 255, 180), width=3)
    
    # [● REC] indicator with blinking red dot
    draw.ellipse([m + 15, m + 20, m + 45, m + 50], fill=(255, 40, 40, 255))
    # Battery icon top-right
    bx = w - m - 80
    by = m + 22
    draw.rectangle([bx, by, bx + 50, by + 26], outline=white, width=4)
    draw.rectangle([bx + 50, by + 7, bx + 55, by + 19], fill=white)
    draw.rectangle([bx + 6, by + 6, bx + 40, by + 20], fill=(50, 230, 80, 255))  # green battery bar
    
    img.save(os.path.join(MARCOS_DIR, "overlay_camara_rec_vertical_720.png"), "PNG")
    print("Created: overlay_camara_rec_vertical_720.png")

# 5. Viewfinder Camera REC Overlay (1280x720 Horizontal)
def gen_viewfinder_horizontal():
    w, h = 1280, 720
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    m = 50
    arm = 70
    lw = 6
    white = (255, 255, 255, 230)
    
    draw.line([(m, m), (m + arm, m)], fill=white, width=lw)
    draw.line([(m, m), (m, m + arm)], fill=white, width=lw)
    draw.line([(w - m - arm, m), (w - m, m)], fill=white, width=lw)
    draw.line([(w - m, m), (w - m, m + arm)], fill=white, width=lw)
    draw.line([(m, h - m), (m + arm, h - m)], fill=white, width=lw)
    draw.line([(m, h - m - arm), (m, h - m)], fill=white, width=lw)
    draw.line([(w - m - arm, h - m), (w - m, h - m)], fill=white, width=lw)
    draw.line([(w - m, h - m - arm), (w - m, h - m)], fill=white, width=lw)
    
    cx, cy = w // 2, h // 2
    c_len = 30
    draw.line([(cx - c_len, cy), (cx + c_len, cy)], fill=(255, 255, 255, 180), width=3)
    draw.line([(cx, cy - c_len), (cx, cy + c_len)], fill=(255, 255, 255, 180), width=3)
    
    draw.ellipse([m + 20, m + 20, m + 50, m + 50], fill=(255, 40, 40, 255))
    bx = w - m - 80
    by = m + 22
    draw.rectangle([bx, by, bx + 50, by + 26], outline=white, width=4)
    draw.rectangle([bx + 50, by + 7, bx + 55, by + 19], fill=white)
    draw.rectangle([bx + 6, by + 6, bx + 40, by + 20], fill=(50, 230, 80, 255))
    
    img.save(os.path.join(MARCOS_DIR, "overlay_camara_rec_horizontal_720.png"), "PNG")
    print("Created: overlay_camara_rec_horizontal_720.png")

# 6. Cinemascope 2.39:1 Letterbox Bars (1280x720)
def gen_letterbox():
    w, h = 1280, 720
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Cinemascope target height for 1280 is: 1280 / 2.39 = ~535px
    # Black bars height: (720 - 535) / 2 = ~92px
    bar_h = 92
    draw.rectangle([0, 0, w, bar_h], fill=(0, 0, 0, 255))
    draw.rectangle([0, h - bar_h, w, h], fill=(0, 0, 0, 255))
    img.save(os.path.join(MARCOS_DIR, "barras_negras_cinemascope_1280x720.png"), "PNG")
    print("Created: barras_negras_cinemascope_1280x720.png")

if __name__ == "__main__":
    gen_thug_life()
    gen_comic_bubble()
    gen_thought_bubble()
    gen_viewfinder_vertical()
    gen_viewfinder_horizontal()
    gen_letterbox()
    print("All visual overlays generated successfully!")
