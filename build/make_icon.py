"""Gera o ícone placeholder do aplicativo em PNG/ICO/ICNS.

Uso:
    poetry run python build/make_icon.py

Gera em ``assets/``:
    - icon.png  (1024x1024, base)
    - icon.ico  (multi-size para Windows)
    - icon.icns (para macOS, apenas quando rodando no macOS com iconutil)

No Linux/Windows o ``.icns`` não é gerado; substitua manualmente se desejar.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

SIZE = 1024


def _gradient_background(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size), "#1E3A8A")
    draw = ImageDraw.Draw(img)
    top = (76, 139, 245)
    bottom = (30, 58, 138)
    for y in range(size):
        ratio = y / (size - 1)
        r = int(top[0] * (1 - ratio) + bottom[0] * ratio)
        g = int(top[1] * (1 - ratio) + bottom[1] * ratio)
        b = int(top[2] * (1 - ratio) + bottom[2] * ratio)
        draw.line([(0, y), (size, y)], fill=(r, g, b))
    return img


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def generate_png(path: Path) -> Path:
    img = _gradient_background(SIZE).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Recorte arredondado (máscara de cantos suaves)
    radius = int(SIZE * 0.22)
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SIZE, SIZE), radius=radius, fill=255)
    rounded = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    rounded.paste(img, (0, 0), mask=mask)
    img = rounded
    draw = ImageDraw.Draw(img)

    font = _load_font(int(SIZE * 0.62))
    text = "$"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (SIZE - tw) // 2 - bbox[0]
    y = (SIZE - th) // 2 - bbox[1] - int(SIZE * 0.02)
    draw.text((x + 6, y + 6), text, font=font, fill=(0, 0, 0, 90))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    img.save(path, format="PNG")
    return path


def generate_ico(png_path: Path, ico_path: Path) -> None:
    img = Image.open(png_path)
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ico_path, format="ICO", sizes=sizes)


def generate_icns(png_path: Path, icns_path: Path) -> bool:
    """Usa o ``iconutil`` do macOS; retorna False silenciosamente em outros OSs."""
    if sys.platform != "darwin" or shutil.which("iconutil") is None:
        return False

    iconset = icns_path.with_suffix(".iconset")
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir()
    specs = [
        (16, 1), (16, 2), (32, 1), (32, 2),
        (128, 1), (128, 2), (256, 1), (256, 2),
        (512, 1), (512, 2),
    ]
    src = Image.open(png_path)
    for base, scale in specs:
        size = base * scale
        resized = src.resize((size, size), Image.LANCZOS)
        suffix = "" if scale == 1 else "@2x"
        resized.save(iconset / f"icon_{base}x{base}{suffix}.png", format="PNG")

    result = subprocess.run(
        ["iconutil", "-c", "icns", str(iconset), "-o", str(icns_path)],
        capture_output=True, text=True,
    )
    shutil.rmtree(iconset)
    if not icns_path.exists():
        print(result.stdout)
        print(result.stderr)
        return False
    return True


def main() -> None:
    png = ASSETS / "icon.png"
    ico = ASSETS / "icon.ico"
    icns = ASSETS / "icon.icns"

    print(f"Gerando {png}...")
    generate_png(png)
    print(f"Gerando {ico}...")
    generate_ico(png, ico)
    print(f"Gerando {icns}...")
    if generate_icns(png, icns):
        print("  OK")
    else:
        print("  pulado (requer macOS com iconutil)")
    print("Concluído.")


if __name__ == "__main__":
    main()
