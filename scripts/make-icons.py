"""Crta ikonicu igrice (tvrđava + viteška kaciga) i snima je u sve potrebne veličine.
Pokretanje iz korena repozitorijuma:  python3 scripts/make-icons.py
"""
import os
from PIL import Image, ImageDraw

S = 1024


def draw_icon():
    base = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=220, fill=(19, 24, 51, 255))
    d.ellipse([170, 120, 860, 810], fill=(40, 50, 100, 255))

    stone, dark, roof = (133, 120, 128, 255), (85, 73, 79, 255), (255, 155, 46, 255)
    d.rectangle([230, 560, 790, 860], fill=stone)
    for x in range(230, 790, 70):
        d.rectangle([x, 520, x + 40, 560], fill=stone)
    for tx in (170, 690):
        d.rectangle([tx, 430, tx + 160, 860], fill=stone)
        d.polygon([(tx - 20, 430), (tx + 80, 290), (tx + 180, 430)], fill=roof)
        d.rounded_rectangle([tx + 58, 500, tx + 102, 570], radius=22, fill=(255, 215, 94, 255))
    d.rectangle([230, 850, 790, 860], fill=dark)
    d.rectangle([420, 700, 604, 860], fill=(42, 26, 20, 255))
    d.ellipse([420, 610, 604, 794], fill=(42, 26, 20, 255))
    d.rectangle([60, 860, 964, 964], fill=(82, 192, 67, 255))

    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=220, fill=255)
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    out.paste(base, (0, 0), mask)

    # viteška kaciga sa perjanicom
    d = ImageDraw.Draw(out)
    cx, cy = 512, 470
    d.polygon([(cx - 30, cy - 150), (cx - 80, cy - 300), (cx - 250, cy - 270),
               (cx - 120, cy - 210), (cx - 70, cy - 150)], fill=(255, 198, 43, 255))
    d.rounded_rectangle([cx - 170, cy - 170, cx + 170, cy + 150], radius=120, fill=(201, 206, 216, 255))
    d.rounded_rectangle([cx - 170, cy - 40, cx + 170, cy + 150], radius=40, fill=(201, 206, 216, 255))
    d.rectangle([cx - 150, cy - 10, cx + 150, cy + 20], fill=(30, 30, 40, 255))
    d.rectangle([cx - 12, cy + 20, cx + 12, cy + 120], fill=(154, 163, 181, 255))
    d.rectangle([cx - 170, cy - 60, cx + 170, cy - 40], fill=(154, 163, 181, 255))
    d.ellipse([cx - 120, cy - 150, cx - 60, cy - 110], fill=(233, 236, 242, 255))
    return out


def main():
    icon = draw_icon()
    os.makedirs('docs', exist_ok=True)
    icon.resize((512, 512), Image.LANCZOS).save('icon.png')
    icon.resize((512, 512), Image.LANCZOS).save('docs/icon-512.png')
    sizes = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
    for name, size in sizes.items():
        folder = f'android/app/src/main/res/mipmap-{name}'
        os.makedirs(folder, exist_ok=True)
        icon.resize((size, size), Image.LANCZOS).save(f'{folder}/ic_launcher.png')
    print('Ikonice su napravljene.')


if __name__ == '__main__':
    main()
