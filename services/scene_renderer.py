"""
Draws storyboard scenes as 1080x1920 images with Pillow.

Screen zones (9:16, YouTube Shorts safe areas):
    y    0-260   top UI area: only the progress bar
    y  320-1260  scene content
    y 1320-1520  captions (drawn by video_generator)
    y 1520-1920  bottom UI area: kept empty
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

import config
from models.state import Scene


WIDTH = config.VIDEO_WIDTH
HEIGHT = config.VIDEO_HEIGHT

MARGIN = 90
CONTENT_TOP = 320
CONTENT_BOTTOM = 1260
CONTENT_WIDTH = WIDTH - 2 * MARGIN

THEMES = {
    "navy":   {"top": (11, 22, 40),  "bottom": (27, 52, 88),  "accent": (46, 204, 113), "accent2": (245, 166, 35), "text": (255, 255, 255), "muted": (170, 184, 204)},
    "teal":   {"top": (6, 40, 46),   "bottom": (12, 92, 99),  "accent": (255, 209, 102), "accent2": (239, 71, 111), "text": (255, 255, 255), "muted": (176, 214, 214)},
    "purple": {"top": (30, 14, 54),  "bottom": (74, 36, 120), "accent": (0, 220, 210),   "accent2": (255, 140, 66), "text": (255, 255, 255), "muted": (200, 184, 230)},
    "sunset": {"top": (52, 18, 40),  "bottom": (160, 60, 60), "accent": (255, 214, 102), "accent2": (120, 220, 255), "text": (255, 255, 255), "muted": (246, 200, 190)},
    "forest": {"top": (10, 36, 24),  "bottom": (28, 84, 56),  "accent": (190, 242, 100), "accent2": (255, 183, 77), "text": (255, 255, 255), "muted": (180, 214, 190)},
}

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


# Shared with the visual and review agents so they plan and judge only
# what can actually be drawn
RENDERER_CAPABILITIES = """\
- Each scene is one still card (with a slow pan) on a gradient background in the chosen color theme, with a progress bar at the top.
- Layouts draw only their text fields: title (big headline), stat (huge number + headline), bullets (headline + dot list), bar_chart (headline + horizontal bars in one color, labelled, values shown with chart_unit), quote (large quotation mark + headline), outro (headline + a "Follow for more" button).
- If "source" is set, a small "Source: ..." credit is shown under the content.
- The narration is burned in as captions of a few words at a time, timed to the voice-over.
- There are no icons, illustrations, photos, maps, arrows, annotations or animations other than these."""


@lru_cache(maxsize=None)
def get_font(size: int) -> ImageFont.FreeTypeFont:

    for path in [config.FONT_PATH, *FONT_CANDIDATES]:
        if path and Path(path).exists():
            return ImageFont.truetype(path, size)

    # Pillow's built-in scalable font
    return ImageFont.load_default(size=size)


# ------------------------------------------------------------------
# Text helpers
# ------------------------------------------------------------------


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> List[str]:

    lines: List[str] = []

    for word in text.split():
        candidate = f"{lines[-1]} {word}" if lines else word

        if lines and draw.textlength(candidate, font=font) <= max_width:
            lines[-1] = candidate
        else:
            lines.append(word)

    return lines


def fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    max_lines: int,
    start_size: int,
    min_size: int = 36,
) -> Tuple[ImageFont.FreeTypeFont, List[str]]:
    """
    Largest font size (stepping down from start_size) at which the text
    wraps into at most max_lines lines that each fit max_width.
    """

    size = start_size

    while True:
        font = get_font(size)
        lines = _wrap(draw, text, font, max_width)

        fits = len(lines) <= max_lines and all(
            draw.textlength(line, font=font) <= max_width for line in lines
        )

        if fits or size <= min_size:
            return font, lines[:max_lines]

        size -= 4


def draw_lines(
    draw: ImageDraw.ImageDraw,
    lines: List[str],
    font,
    top: int,
    fill,
    x: int = WIDTH // 2,
    anchor: str = "ma",
    spacing: float = 1.18,
) -> int:
    """
    Draw lines starting at `top`; returns the y below the last line.
    """

    line_height = int(font.size * spacing)

    for number, line in enumerate(lines):
        draw.text((x, top + number * line_height), line, font=font, fill=fill, anchor=anchor)

    return top + len(lines) * line_height


def _block_height(font, lines: List[str], spacing: float = 1.18) -> int:
    return int(font.size * spacing) * len(lines)


# ------------------------------------------------------------------
# Background and decorations
# ------------------------------------------------------------------


def _background(theme: dict, scene_number: int, total_scenes: int) -> Image.Image:

    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    top, bottom = theme["top"], theme["bottom"]
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line([(0, y), (WIDTH, y)], fill=color)

    # Soft decorative circles; position varies per scene
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    offset = (scene_number * 173) % 400

    overlay_draw.ellipse(
        [WIDTH - 420 + offset // 4, 120 + offset, WIDTH + 260, 800 + offset],
        fill=(*theme["accent"], 28),
    )
    overlay_draw.ellipse(
        [-300, HEIGHT - 900 - offset // 2, 380, HEIGHT - 220 - offset // 2],
        fill=(*theme["accent2"], 22),
    )

    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)

    # Progress bar: one segment per scene
    gap = 12
    segment = (CONTENT_WIDTH - gap * (total_scenes - 1)) / total_scenes
    for number in range(total_scenes):
        x0 = MARGIN + number * (segment + gap)
        done = number < scene_number
        draw.rounded_rectangle(
            [x0, 268, x0 + segment, 280],
            radius=6,
            fill=theme["accent"] if done else tuple(c // 2 for c in theme["muted"]),
        )

    return image


# ------------------------------------------------------------------
# Layouts
# ------------------------------------------------------------------


def _layout_title(draw, scene: Scene, theme: dict) -> None:

    font, lines = fit_text(draw, scene.headline, CONTENT_WIDTH, 5, 124)
    height = _block_height(font, lines)
    top = (CONTENT_TOP + CONTENT_BOTTOM) // 2 - height // 2 - 40

    bottom = draw_lines(draw, lines, font, top, theme["text"])
    draw.rounded_rectangle(
        [WIDTH // 2 - 110, bottom + 40, WIDTH // 2 + 110, bottom + 56],
        radius=8,
        fill=theme["accent"],
    )


def _layout_stat(draw, scene: Scene, theme: dict) -> None:

    stat_font, stat_lines = fit_text(draw, scene.stat_value, CONTENT_WIDTH, 1, 300, 120)
    label_font, label_lines = fit_text(draw, scene.headline, CONTENT_WIDTH, 4, 76)

    total = _block_height(stat_font, stat_lines, 1.0) + 60 + _block_height(label_font, label_lines)
    top = (CONTENT_TOP + CONTENT_BOTTOM) // 2 - total // 2

    bottom = draw_lines(draw, stat_lines, stat_font, top, theme["accent"], spacing=1.0)
    draw_lines(draw, label_lines, label_font, bottom + 60, theme["text"])


def _layout_bullets(draw, scene: Scene, theme: dict) -> None:

    head_font, head_lines = fit_text(draw, scene.headline, CONTENT_WIDTH, 3, 84)
    y = draw_lines(draw, head_lines, head_font, CONTENT_TOP + 40, theme["text"]) + 70

    bullets = scene.bullets[:4]
    text_left = MARGIN + 70
    text_width = WIDTH - MARGIN - text_left

    for bullet in bullets:
        font, lines = fit_text(draw, bullet, text_width, 2, 60, 40)
        radius = 14
        center_y = y + font.size // 2 + 4
        draw.ellipse(
            [MARGIN + 10, center_y - radius, MARGIN + 10 + 2 * radius, center_y + radius],
            fill=theme["accent"],
        )
        y = draw_lines(draw, lines, font, y, theme["text"], x=text_left, anchor="la") + 50


def _layout_bar_chart(draw, scene: Scene, theme: dict) -> None:

    head_font, head_lines = fit_text(draw, scene.headline, CONTENT_WIDTH, 3, 80)
    y = draw_lines(draw, head_lines, head_font, CONTENT_TOP + 20, theme["text"]) + 60

    pairs = list(zip(scene.chart_labels, scene.chart_values))[:5]
    max_value = max(abs(value) for _, value in pairs) or 1

    label_font = get_font(48)
    value_font = get_font(52)
    bar_height = 64
    row_height = min(200, (CONTENT_BOTTOM - 60 - y) // len(pairs))
    max_bar = CONTENT_WIDTH - 200

    decimals = 0 if all(float(value).is_integer() for _, value in pairs) else 1

    for label, value in pairs:
        draw.text((MARGIN, y), label, font=label_font, fill=theme["muted"], anchor="la")

        bar_top = y + 62
        bar_width = max(16, int(max_bar * abs(value) / max_value))
        draw.rounded_rectangle(
            [MARGIN, bar_top, MARGIN + bar_width, bar_top + bar_height],
            radius=14,
            fill=theme["accent"],
        )
        draw.text(
            (MARGIN + bar_width + 24, bar_top + bar_height // 2),
            _format_number(value, decimals, scene.chart_unit),
            font=value_font,
            fill=theme["text"],
            anchor="lm",
        )
        y += row_height


def _layout_quote(draw, scene: Scene, theme: dict) -> None:

    font, lines = fit_text(draw, scene.headline, CONTENT_WIDTH, 6, 96)
    height = _block_height(font, lines)
    top = (CONTENT_TOP + CONTENT_BOTTOM) // 2 - height // 2 + 60

    draw.text((WIDTH // 2, top - 40), "\u201c", font=get_font(300), fill=theme["accent"], anchor="ms")
    draw_lines(draw, lines, font, top, theme["text"])


def _layout_outro(draw, scene: Scene, theme: dict) -> None:

    font, lines = fit_text(draw, scene.headline, CONTENT_WIDTH, 5, 108)
    height = _block_height(font, lines)
    top = (CONTENT_TOP + CONTENT_BOTTOM) // 2 - height // 2 - 80

    bottom = draw_lines(draw, lines, font, top, theme["text"])

    pill_font = get_font(52)
    label = "Follow for more"
    pill_width = int(draw.textlength(label, font=pill_font)) + 100
    pill_top = bottom + 70
    draw.rounded_rectangle(
        [WIDTH // 2 - pill_width // 2, pill_top, WIDTH // 2 + pill_width // 2, pill_top + 110],
        radius=55,
        fill=theme["accent"],
    )
    draw.text((WIDTH // 2, pill_top + 55), label, font=pill_font, fill=theme["top"], anchor="mm")


LAYOUTS = {
    "title": _layout_title,
    "stat": _layout_stat,
    "bullets": _layout_bullets,
    "bar_chart": _layout_bar_chart,
    "quote": _layout_quote,
    "outro": _layout_outro,
}


def _effective_layout(scene: Scene) -> str:
    """
    Fall back to the title layout when the scene lacks the data its
    layout needs.
    """

    if scene.layout == "stat" and not scene.stat_value.strip():
        return "title"
    if scene.layout == "bullets" and not scene.bullets:
        return "title"
    if scene.layout == "bar_chart" and (
        len(scene.chart_labels) < 2
        or len(scene.chart_labels) != len(scene.chart_values)
    ):
        return "bullets" if scene.bullets else "title"

    return scene.layout


def _format_number(value: float, decimals: int, unit: str) -> str:

    number = f"{value:,.{decimals}f}"
    unit = unit.strip()

    if not unit:
        return number
    # Symbols attach directly ("43.0%"), words get a space ("47 crore")
    return f"{number}{unit}" if len(unit) == 1 and not unit.isalnum() else f"{number} {unit}"


def _draw_source(draw, source: str, theme: dict) -> None:

    if not source.strip():
        return

    font, lines = fit_text(draw, f"Source: {source.strip()}", CONTENT_WIDTH, 2, 34, 26)
    top = CONTENT_BOTTOM - _block_height(font, lines)
    draw_lines(draw, lines, font, top, theme["muted"])


def render_scene(
    scene: Scene,
    color_theme: str,
    total_scenes: int,
    output_path: Path,
) -> str:

    theme = THEMES.get(color_theme, THEMES["navy"])

    image = _background(theme, scene.index, total_scenes)
    draw = ImageDraw.Draw(image)

    LAYOUTS[_effective_layout(scene)](draw, scene, theme)
    _draw_source(draw, scene.source, theme)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)

    return str(output_path)


def render_caption(text: str) -> Image.Image:
    """
    A caption box (transparent RGBA image, full video width) for
    burning into the video.
    """

    measure = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    font, lines = fit_text(measure, text, CONTENT_WIDTH - 60, 2, 58, 40)

    line_height = int(font.size * 1.25)
    box_height = line_height * len(lines) + 50

    image = Image.new("RGBA", (WIDTH, box_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    box_width = max(int(draw.textlength(line, font=font)) for line in lines) + 70
    draw.rounded_rectangle(
        [WIDTH // 2 - box_width // 2, 0, WIDTH // 2 + box_width // 2, box_height],
        radius=28,
        fill=(0, 0, 0, 170),
    )

    for number, line in enumerate(lines):
        draw.text(
            (WIDTH // 2, 25 + number * line_height),
            line,
            font=font,
            fill=(255, 255, 255, 255),
            anchor="ma",
        )

    return image
