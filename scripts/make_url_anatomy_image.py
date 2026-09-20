"""Render docs/images/url-anatomy.png.

The diagram explains which part of a resolved Google Maps URL holds the real
marker position, using a public landmark (Candi Borobudur) as the example.

    python scripts/make_url_anatomy_image.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images" / "url-anatomy.png"

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

BG = "#12161c"
FG = "#c9d4e3"
DIM = "#66748a"
CAMERA = "#e0a33a"     # amber - approximate
PIN = "#3fa66b"        # green - exact

URL_PARTS = [
    ("https://www.google.com/maps/place/Candi+Borobudur", FG, None),
    ("/@-7.6078574,110.2038233", FG, "camera"),
    (",17z/data=!3m1!4b1!4m6!3m5!1s0x0:0x0!8m2", DIM, None),
    ("!3d-7.6078738", FG, "lat"),
    ("!4d110.2037342", FG, "lng"),
]

WIDTH = 1180
PAD = 34
LINE_H = 30
FONT_SIZE = 17


def main() -> None:
    mono = ImageFont.truetype(MONO, FONT_SIZE)
    mono_bold = ImageFont.truetype(MONO_BOLD, FONT_SIZE)
    sans = ImageFont.truetype(SANS, 15)
    sans_bold = ImageFont.truetype(SANS_BOLD, 17)

    char_w = mono.getlength("M")
    max_chars = int((WIDTH - 2 * PAD) / char_w)

    # Flatten the URL into characters tagged with their role, then wrap.
    tagged = [(ch, colour, role) for text, colour, role in URL_PARTS for ch in text]
    lines: list[list[tuple[str, str, str | None]]] = [
        tagged[i:i + max_chars] for i in range(0, len(tagged), max_chars)
    ]

    height = PAD + 44 + len(lines) * LINE_H + 150
    img = Image.new("RGB", (WIDTH, height), BG)
    draw = ImageDraw.Draw(img)

    draw.text((PAD, PAD - 8), "What a resolved Google Maps URL looks like",
              font=sans_bold, fill=FG)

    y = PAD + 30
    role_spans: dict[str, tuple[int, int, int]] = {}  # role -> (x0, x1, y)

    for line in lines:
        x = PAD
        for ch, colour, role in line:
            highlight = role in ("camera", "lat", "lng")
            if role in ("lat", "lng"):
                box = PIN
            elif role == "camera":
                box = CAMERA
            else:
                box = None

            width_ch = mono.getlength(ch)
            if highlight:
                draw.rectangle([x - 1, y - 4, x + width_ch + 1, y + FONT_SIZE + 7], fill=box)
                draw.text((x, y), ch, font=mono_bold, fill="#0e1116")
                first, last, _ = role_spans.get(role, (x, x, y))
                role_spans[role] = (min(first, x), max(last, x + width_ch), y)
            else:
                draw.text((x, y), ch, font=mono, fill=colour)
            x += width_ch
        y += LINE_H

    legend_y = y + 18
    for colour, title, body in [
        (PIN, "!3d / !4d  -  the map pin",
         "The exact marker. This is what the extractor takes first."),
        (CAMERA, "@lat,lng  -  the camera",
         "Where the viewport is centred. Close, but a few metres off."),
    ]:
        draw.rectangle([PAD, legend_y + 3, PAD + 14, legend_y + 17], fill=colour)
        draw.text((PAD + 26, legend_y), title, font=sans_bold, fill=FG)
        draw.text((PAD + 26, legend_y + 23), body, font=sans, fill=DIM)
        legend_y += 60

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(f"Wrote {OUT} ({img.width}x{img.height})")


if __name__ == "__main__":
    main()
