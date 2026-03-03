"""Generate Wardrop extension icons at 16x16, 48x48, 128x128."""
from PIL import Image, ImageDraw, ImageFont

SIZES = [16, 48, 128]
BG_COLOR = (99, 102, 241)       # #6366f1 (indigo)
TEXT_COLOR = (255, 255, 255)     # white


def create_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded rectangle background
    radius = max(2, size // 6)
    draw.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=radius,
        fill=BG_COLOR,
    )

    # Draw "W" letter
    font_size = int(size * 0.6)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), "W", font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2
    y = (size - text_h) // 2 - bbox[1]

    draw.text((x, y), "W", font=font, fill=TEXT_COLOR)
    return img


for s in SIZES:
    icon = create_icon(s)
    icon.save(f"icon{s}.png")
    print(f"Created icon{s}.png")
