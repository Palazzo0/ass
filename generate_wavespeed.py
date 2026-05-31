"""
Dr. P's Corner — World Menstrual Hygiene Day
WaveSpeed AI Video Generator

Generates each scene via WaveSpeed Wan 2.1 API (I2V or T2V),
then composites motion-graphics overlays using PIL and assembles
the final 9:16 60-second video with FFmpeg.

Usage:
    python generate_wavespeed.py --image /path/to/drp.png [--output out.mp4]

Environment:
    WAVESPEED_API_KEY  — WaveSpeed live API key (falls back to --api-key arg)
"""

import argparse
import base64
import io
import math
import os
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Load .env if present (so `python generate_wavespeed.py` works out of the box)
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# ─── CONFIG ───────────────────────────────────────────────────────────────────
W, H = 1080, 1920
FPS = 24
WAVESPEED_BASE = "https://api.wavespeed.ai/api/v3"

ASSETS_DIR = Path("/home/user/ass")

FONT_PATHS = {
    "serif": ["/root/.fonts/PlayfairDisplay-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"],
    "sans":  ["/root/.fonts/DMSans-Medium.ttf",        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"],
    "round": ["/root/.fonts/Nunito-SemiBold.ttf",      "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"],
}

# ─── BRAND PALETTE ────────────────────────────────────────────────────────────
BEIGE      = (245, 237, 224)
SOFT_PINK  = (242, 184, 198)
LILAC      = (200, 180, 226)
NUDE_BROWN = (160, 120,  90)
CREAM      = (255, 248, 242)
DEEP_ROSE  = (212,  96, 122)
WARM_AMBER = (230, 180, 130)
DARK_BROWN = (100,  65,  45)
WHITE      = (255, 255, 255)

# ─── SCENE DEFINITIONS ────────────────────────────────────────────────────────
# Each scene: (start_sec, end_sec, i2v_prompt, t2v_fallback_prompt)
SCENES = [
    (0, 3,
     "Warm professional African woman doctor, gentle welcoming smile, soft warm studio lighting, slight head nod, subtle breathing, cinematic 9:16 vertical portrait",
     "Soft warm beige-to-lilac gradient background with floating bokeh orbs, gentle ambient motion, 9:16 vertical, cinematic brand video"),

    (3, 11,
     "Professional woman doctor speaking calmly and confidently, subtle hand gestures, warm studio light, dignified expression, cinematic 9:16 vertical",
     "Warm beige gradient background, soft pink and lilac bokeh floating slowly, elegant ambient motion, 9:16 vertical brand video"),

    (11, 16,
     "Warm professional woman doctor, hopeful uplifting expression, slight forward lean, encouraging body language, soft warm lighting, 9:16 vertical cinematic",
     "Lilac-to-beige gradient, golden light rays, soft sparkle particles rising, hopeful warm atmosphere, 9:16 vertical brand video"),

    (16, 21,
     "Professional woman doctor, empathetic gentle expression, supportive body language, warm studio lighting, slight head tilt, cinematic 9:16 vertical portrait",
     "Soft pink and lilac gradient background, gentle floating hearts and light particles, warm empathetic mood, 9:16 vertical brand video"),

    (21, 28,
     "Professional woman doctor, tender caring expression, hands clasped, warm amber studio light, emotional sincerity, cinematic 9:16 vertical",
     "Warm amber-lilac gradient, soft glowing orbs, gentle floating light particles, emotional tender mood, 9:16 vertical brand video"),

    (28, 38,
     "Professional woman doctor, confident empowering expression, slight forward presence, clear direct gaze, warm studio lighting, cinematic 9:16 vertical",
     "Deep rose-to-beige gradient, bold energy particles, dynamic light sweep, empowering mood, 9:16 vertical brand video"),

    (38, 48,
     "Professional woman doctor, dignified regal expression, gentle warm glow, elevated presence, deep warm studio lighting, cinematic 9:16 vertical portrait",
     "Cream-lilac gradient, golden shimmer light sweeping, floating dignity words, regal warm atmosphere, 9:16 vertical brand video"),

    (48, 60,
     "Professional woman doctor, warm closing smile, gracious presence, soft studio lighting, gentle fade to elegant, cinematic 9:16 vertical portrait",
     "Lilac-to-beige gradient, falling hibiscus petals, soft warm glow, elegant brand closing screen, 9:16 vertical"),
]

# ─── FONT LOADER ──────────────────────────────────────────────────────────────
_font_cache: dict = {}

def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    size = max(1, size)
    key = (kind, size)
    if key not in _font_cache:
        for path in FONT_PATHS.get(kind, []):
            if os.path.exists(path):
                _font_cache[key] = ImageFont.truetype(path, size)
                break
        else:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]

# ─── EASING ───────────────────────────────────────────────────────────────────
def ease_out(t: float) -> float:
    return 1 - (1 - max(0.0, min(1.0, t))) ** 3

def ease_bounce(t: float) -> float:
    t = max(0.0, min(1.0, t))
    if t < 0.7273:
        return 7.5625 * t * t
    elif t < 0.9091:
        t -= 0.8182
        return 7.5625 * t * t + 0.75
    elif t < 0.9773:
        t -= 0.9545
        return 7.5625 * t * t + 0.9375
    else:
        t -= 0.9886
        return 7.5625 * t * t + 0.984375

def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))

def anim_t(f: int, start_sec: float, dur_sec: float) -> float:
    return clamp((f / FPS - start_sec) / dur_sec)

def alpha_t(f: int, in_sec: float, out_sec: float, fade: float = 0.3) -> float:
    total = out_sec - in_sec
    t = f / FPS - in_sec
    if t <= 0:
        return 0.0
    if t < fade:
        return ease_out(t / fade)
    if t > total - fade:
        return ease_out((total - t) / fade)
    if t > total:
        return 0.0
    return 1.0

# ─── DRAWING HELPERS ──────────────────────────────────────────────────────────
def rgba(c, a: int = 255):
    return (*c[:3], a)

def blend(base: Image.Image, layer: Image.Image) -> Image.Image:
    if base.mode != "RGBA":
        base = base.convert("RGBA")
    if layer.mode != "RGBA":
        layer = layer.convert("RGBA")
    return Image.alpha_composite(base, layer)

def text_center(draw, text: str, cx: int, cy: int, fnt, color, shadow: bool = True):
    bb = fnt.getbbox(text)
    x = cx - (bb[2] - bb[0]) // 2
    y = cy - (bb[3] - bb[1]) // 2
    if shadow:
        draw.text((x + 2, y + 2), text, font=fnt, fill=rgba(DARK_BROWN, 50))
    draw.text((x, y), text, font=fnt, fill=rgba(color))

def glow_text(img: Image.Image, text: str, cx: int, cy: int, fnt,
              color, glow_color=None, glow_r: int = 20) -> Image.Image:
    glow_color = glow_color or color
    bb = fnt.getbbox(text)
    x = cx - (bb[2] - bb[0]) // 2
    y = cy - (bb[3] - bb[1]) // 2
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for off in range(glow_r, 0, -2):
        a = int(110 * (1 - off / glow_r) ** 2)
        gd.text((x, y), text, font=fnt, fill=(*glow_color[:3], a))
    glow = glow.filter(ImageFilter.GaussianBlur(glow_r // 3))
    img = blend(img, glow)
    d = ImageDraw.Draw(img)
    d.text((x + 2, y + 2), text, font=fnt, fill=rgba(DARK_BROWN, 70))
    d.text((x, y), text, font=fnt, fill=rgba(color))
    return img

def draw_heart(draw, cx: int, cy: int, size: int, color=DEEP_ROSE, alpha: int = 220):
    if size < 4:
        return
    pts = []
    for i in range(60):
        t = math.pi * 2 * i / 60
        x = int(size * 0.85 * math.sin(t) ** 3)
        y = int(-size * (0.8 * math.cos(t) - 0.31 * math.cos(2*t)
                          - 0.12 * math.cos(3*t) - 0.04 * math.cos(4*t)))
        pts.append((cx + x, cy + y))
    if len(pts) >= 3:
        draw.polygon(pts, fill=rgba(color, alpha))

def draw_sparkle(draw, cx: int, cy: int, size: int, color=SOFT_PINK, alpha: int = 200):
    for angle in [0, math.pi/2, math.pi, 3*math.pi/2]:
        ex = cx + int(math.cos(angle) * size)
        ey = cy + int(math.sin(angle) * size)
        draw.line([cx, cy, ex, ey], fill=rgba(color, alpha), width=3)
    for angle in [math.pi/4, 3*math.pi/4, 5*math.pi/4, 7*math.pi/4]:
        ex = cx + int(math.cos(angle) * size * 0.6)
        ey = cy + int(math.sin(angle) * size * 0.6)
        draw.line([cx, cy, ex, ey], fill=rgba(color, alpha), width=2)

def draw_pad(draw, cx: int, cy: int, size: int, p: float = 1.0,
             color=SOFT_PINK, outline=NUDE_BROWN):
    w = int(size * 0.6 * p)
    h = int(size * p)
    if w < 4 or h < 4:
        return
    r = min(w, h) // 3
    draw.rounded_rectangle([cx-w//2, cy-h//2, cx+w//2, cy+h//2],
                            radius=r, fill=rgba(color, 220), outline=rgba(outline, 200), width=3)
    wing_w = int(w * 0.35 * p)
    wing_h = int(h * 0.4 * p)
    if wing_w > 2:
        draw.rounded_rectangle([cx-w//2-wing_w, cy-wing_h//2, cx-w//2+4, cy+wing_h//2],
                                radius=4, fill=rgba(color, 160), outline=rgba(outline, 160), width=2)
        draw.rounded_rectangle([cx+w//2-4, cy-wing_h//2, cx+w//2+wing_w, cy+wing_h//2],
                                radius=4, fill=rgba(color, 160), outline=rgba(outline, 160), width=2)

def draw_hibiscus(draw, cx: int, cy: int, size: int, unfurl: float = 1.0, color=LILAC):
    petal_len = int(size * 0.5 * unfurl)
    if petal_len < 3:
        return
    petal_w = int(size * 0.22 * unfurl)
    for i in range(5):
        angle = math.pi * 2 * i / 5 - math.pi / 2
        px = cx + int(math.cos(angle) * petal_len * 0.6)
        py = cy + int(math.sin(angle) * petal_len * 0.6)
        pts = [(px + int(math.cos(math.pi*2*j/16)*petal_w),
                py + int(math.sin(math.pi*2*j/16)*petal_len*0.5))
               for j in range(16)]
        if len(pts) >= 3:
            draw.polygon(pts, fill=rgba(color, 200), outline=rgba(NUDE_BROWN, 120))
    draw.ellipse([cx-size//6, cy-size//6, cx+size//6, cy+size//6],
                 fill=rgba(SOFT_PINK, 240), outline=rgba(NUDE_BROWN, 180))

def draw_drop(draw, cx: int, cy: int, size: int, color=DEEP_ROSE):
    if size < 4:
        return
    pts = []
    for i in range(20):
        a = math.pi * 2 * i / 20
        rx = size * (0.45 if a < math.pi else 0.35) * math.sin(a)
        ry = -size * 0.5 * math.cos(a)
        pts.append((cx + int(rx), cy + int(ry)))
    draw.polygon(pts, fill=rgba(color, 200), outline=rgba(DARK_BROWN, 120))

def draw_logo(draw, cx: int, cy: int, scale: float = 1.0, alpha: int = 220):
    f1 = font("serif", int(44 * scale))
    f2 = font("serif", int(28 * scale))
    bb1 = f1.getbbox("Dr. P's")
    bb2 = f2.getbbox("CORNER")
    draw.text((cx - (bb1[2]-bb1[0])//2, cy - int(30*scale)), "Dr. P's",
              font=f1, fill=rgba(NUDE_BROWN, alpha))
    draw.text((cx - (bb2[2]-bb2[0])//2, cy + int(20*scale)), "CORNER",
              font=f2, fill=rgba(DEEP_ROSE, alpha))
    draw_heart(draw, cx, cy + int(58*scale), int(10*scale), DEEP_ROSE, alpha)

def draw_popup_card(img: Image.Image, text: str, cx: int, cy: int, progress: float,
                    color=NUDE_BROWN, bg=CREAM, border=SOFT_PINK, strike: bool = False) -> Image.Image:
    if progress <= 0:
        return img
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    fnt = font("sans", 42)
    bb = fnt.getbbox(text)
    tw = bb[2] - bb[0] + 60
    th = bb[3] - bb[1] + 36
    sw, sh = int(tw * progress), int(th * progress)
    if sw < 10 or sh < 10:
        return img
    a = int(240 * min(progress * 3, 1.0))
    d.rounded_rectangle([cx-sw//2, cy-sh//2, cx+sw//2, cy+sh//2],
                         radius=20, fill=rgba(bg, a), outline=rgba(border, a), width=4)
    if progress > 0.6:
        ta = int(255 * (progress - 0.6) / 0.4)
        d.text((cx - (bb[2]-bb[0])//2, cy - (bb[3]-bb[1])//2), text,
               font=fnt, fill=rgba(color, ta))
        if strike and progress > 0.8:
            sa = int(255 * (progress - 0.8) / 0.2)
            lx1 = cx - tw//2 + 20
            lx2 = cx + tw//2 - 20
            d.line([(lx1, cy+2), (lx2, cy+2)], fill=rgba(DEEP_ROSE, sa), width=4)
    return blend(img, layer)

def draw_speech_bubble(draw, cx: int, cy: int, bw: int, bh: int,
                       lines: list, fnt, scale: float = 1.0):
    sw, sh = int(bw * scale), int(bh * scale)
    if sw < 20 or sh < 20:
        return
    draw.rounded_rectangle([cx-sw//2, cy-sh//2, cx+sw//2, cy+sh//2],
                            radius=20, fill=rgba(CREAM, 240), outline=rgba(SOFT_PINK, 220), width=4)
    tail = [(cx+sw//2-10, cy+sh//4), (cx+sw//2+20, cy+sh//2+15), (cx+sw//2-30, cy+sh//2-5)]
    draw.polygon(tail, fill=rgba(CREAM, 240))
    line_h = fnt.getbbox("A")[3] + 10
    start_y = cy - len(lines) * line_h // 2
    for i, line in enumerate(lines):
        bb = fnt.getbbox(line)
        draw.text((cx - (bb[2]-bb[0])//2, start_y + i * line_h), line,
                  font=fnt, fill=rgba(DARK_BROWN))

# ─── OVERLAY COMPOSITOR ───────────────────────────────────────────────────────
def composite_overlay(bg_frame: Image.Image, f: int) -> Image.Image:
    """Apply motion-graphics overlay onto a background frame at position f."""
    t = f / FPS
    img = bg_frame.convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # ── INTRO 0–3s ────────────────────────────────────────────────────────────
    if t < 3.5:
        cp = ease_out(anim_t(f, 0.2, 0.6))
        ca = int(230 * cp)
        if ca > 10:
            cw, ch = int(460 * cp), int(110 * cp)
            d.rounded_rectangle([W//2-cw//2, 120, W//2+cw//2, 120+ch],
                                 radius=18, fill=rgba(LILAC, ca), outline=rgba(NUDE_BROWN, ca), width=3)
            if cp > 0.7:
                text_center(d, "WORLD MENSTRUAL HYGIENE DAY", W//2, 162, font("sans", 28), NUDE_BROWN, shadow=False)
                text_center(d, "May 28", W//2, 204, font("serif", 44), DEEP_ROSE, shadow=False)

        tp = alpha_t(f, 0.8, 3.5)
        if tp > 0.05:
            fn = font("serif", 58)
            fn2 = font("serif", 48)
            slide = int((1 - ease_out(min(tp * 3, 1.0))) * 40)
            y0 = H // 2 - 160
            bb = fn.getbbox("Dear girls…")
            d.text((W//2 - (bb[2]-bb[0])//2, y0 + slide), "Dear girls…",
                   font=fn, fill=rgba(NUDE_BROWN, int(230*tp)))
            bb2 = fn2.getbbox("and dear mothers…")
            d.text((W//2 - (bb2[2]-bb2[0])//2, y0 + 80 + slide), "and dear mothers…",
                   font=fn2, fill=rgba(DEEP_ROSE, int(200*tp)))

        lp = ease_out(anim_t(f, 0.3, 0.8))
        if lp > 0.1:
            draw_logo(d, W - 130, 120, scale=0.75 * lp, alpha=int(200 * lp))

    # ── "NOT" STATEMENTS 3–11s ────────────────────────────────────────────────
    elif 3 <= t < 11:
        st = t - 3
        pad_p = ease_out(anim_t(f, 3.2, 0.8))
        pad_float = int(math.sin(st * 1.5) * 12)
        draw_pad(d, 130, 600 + pad_float, 90, pad_p)

        hib_p = ease_out(anim_t(f, 4.5, 0.8))
        draw_hibiscus(d, 160, 900 + int(math.sin(st*1.8+2)*8), 70, hib_p)

        img = draw_popup_card(img, "Periods are NOT dirty ✗",   W//2, H//2-220,
                               ease_bounce(clamp((t-3.0)/0.5)) * alpha_t(f, 3.0, 7.5),
                               DARK_BROWN, CREAM, DEEP_ROSE, strike=True)
        img = draw_popup_card(img, "NOT shameful ✗",            W//2, H//2-60,
                               ease_bounce(clamp((t-4.5)/0.5)) * alpha_t(f, 4.5, 6.5),
                               DARK_BROWN, CREAM, LILAC, strike=True)
        img = draw_popup_card(img, "NOT a punishment ✗",        W//2, H//2+100,
                               ease_bounce(clamp((t-6.0)/0.5)) * alpha_t(f, 6.0, 5.0),
                               DARK_BROWN, CREAM, SOFT_PINK, strike=True)

        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        ta = alpha_t(f, 3.2, 7.8)
        if ta > 0.05:
            fn_s = font("serif", 52)
            fn_b = font("sans", 44)
            lines = [("NOT dirty.",       fn_s, DEEP_ROSE),
                     ("NOT shameful.",    fn_s, DEEP_ROSE),
                     ("NOT a punishment.", fn_s, DEEP_ROSE)]
            vis = min(3, int((t-3.2)*1.0)+1)
            for i, (txt, f_, col) in enumerate(lines[:vis]):
                text_center(d, txt, W//2, H-380+i*80, f_, col)

    # ── CONFIDENCE 11–16s ─────────────────────────────────────────────────────
    elif 11 <= t < 16:
        st = t - 11
        line1a = alpha_t(f, 11.2, 4.8)
        confa  = alpha_t(f, 12.8, 3.2)

        if line1a > 0.05:
            text_center(d, "That little girl", W//2, H//2-180, font("sans", 44), NUDE_BROWN)
            text_center(d, "hiding her pad in school?", W//2, H//2-120, font("sans", 42), NUDE_BROWN)
            text_center(d, "She deserves…", W//2, H//2-40, font("serif", 48), DARK_BROWN)

        if confa > 0.05:
            sc = ease_bounce(clamp((t-12.8)/0.6))
            ov2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            img = blend(img, ov)
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)

            fn_c = font("serif", int(80 * sc))
            if sc > 0.05:
                img = glow_text(img.convert("RGBA"), "CONFIDENCE", W//2, H//2+60, fn_c, DEEP_ROSE, LILAC, 25)
                d = ImageDraw.Draw(ov)
            if confa > 0.3:
                for ang in range(0, 360, 45):
                    sx = W//2 + int(math.cos(math.radians(ang))*160)
                    sy = H//2 + 60 + int(math.sin(math.radians(ang))*80)
                    draw_sparkle(d, sx, sy, int(18*confa), LILAC, int(200*confa))

    # ── SUPPORT 16–21s ────────────────────────────────────────────────────────
    elif 16 <= t < 21:
        st = t - 16
        suppa = alpha_t(f, 17.8, 3.2)

        if alpha_t(f, 16.2, 4.8) > 0.05:
            text_center(d, "That teenager", W//2, H//2-180, font("sans", 44), NUDE_BROWN)
            text_center(d, "scared because of stains?", W//2, H//2-120, font("sans", 40), NUDE_BROWN)
            text_center(d, "She deserves…", W//2, H//2-40, font("serif", 48), DARK_BROWN)

        if suppa > 0.05:
            sc = ease_bounce(clamp((t-17.8)/0.6))
            img = blend(img, ov)
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            fn_s = font("serif", int(78 * sc))
            if sc > 0.05:
                img = glow_text(img.convert("RGBA"), "SUPPORT", W//2, H//2+65, fn_s, LILAC, SOFT_PINK, 22)
                d = ImageDraw.Draw(ov)
                ul = clamp((t-18.2)/0.5)
                if ul > 0:
                    bb = fn_s.getbbox("SUPPORT")
                    ulw = bb[2] - bb[0]
                    ux1 = W//2 - ulw//2
                    uly = H//2 + 65 + bb[3]//2 + 8
                    d.line([(ux1, uly), (ux1 + int(ulw*ul), uly)],
                           fill=rgba(DEEP_ROSE, int(220*suppa)), width=5)
            for i in range(3):
                ht = (st - i*0.5) % 3.0
                hy_ = H//2 - int(ht*60) - 20
                ha = int(180 * (1 - ht/3.0) * suppa)
                draw_heart(d, W-160 + [-25, 0, 25][i], hy_, 14, SOFT_PINK, ha)

    # ── CARE 21–28s ───────────────────────────────────────────────────────────
    elif 21 <= t < 28:
        st = t - 21
        carea = alpha_t(f, 22.8, 5.2)

        if alpha_t(f, 21.3, 6.7) > 0.05:
            text_center(d, "That mother", W//2, H//2-260, font("sans", 44), NUDE_BROWN)
            text_center(d, "silently enduring…", W//2, H//2-200, font("sans", 40), NUDE_BROWN)
            text_center(d, "painful periods?", W//2, H//2-148, font("sans", 40), NUDE_BROWN)
            text_center(d, "You deserve…", W//2, H//2-80, font("serif", 48), DARK_BROWN)

        if carea > 0.05:
            sc = ease_bounce(clamp((t-22.8)/0.6))
            img = blend(img, ov)
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            fn_care = font("serif", int(76 * sc))
            if sc > 0.05:
                img = glow_text(img.convert("RGBA"), "CARE.", W//2, H//2+20, fn_care, DEEP_ROSE, SOFT_PINK, 25)
                d = ImageDraw.Draw(ov)
            if carea > 0.4:
                text_center(d, "too.  🤍", W//2, H//2+110, font("serif", 52), NUDE_BROWN)

        # Heart outline drawing itself
        hdp = clamp((t-22.0)/1.5)
        if hdp > 0:
            hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            hld = ImageDraw.Draw(hl)
            for i in range(int(60 * hdp)):
                th = math.pi * 2 * i / 60
                hxi = int(70 * math.sin(th)**3)
                hyi = int(-60*(0.8*math.cos(th)-0.3*math.cos(2*th)-0.1*math.cos(3*th)))
                hld.ellipse([W//2 + hxi - 4, H-520+hyi-4, W//2+hxi+4, H-520+hyi+4],
                             fill=rgba(LILAC, 180))
            img = blend(img, hl)
            d = ImageDraw.Draw(ov)

    # ── CTA / TALK 28–38s ─────────────────────────────────────────────────────
    elif 28 <= t < 38:
        st = t - 28
        wp = ease_out(anim_t(f, 28.2, 0.8))
        if wp > 0.1:
            fn_w = font("serif", 50)
            text_center(d, "STOP WHISPERING", W//2, H//2-280, fn_w, NUDE_BROWN)
            sp = clamp((t-28.6)/0.5)
            if sp > 0:
                bb = fn_w.getbbox("STOP WHISPERING")
                tw_ = bb[2]-bb[0]
                d.line([(W//2-tw_//2, H//2-280), (W//2-tw_//2+int(tw_*sp), H//2-280)],
                       fill=rgba(DEEP_ROSE, 240), width=5)

        bsc = ease_bounce(clamp((t-29.0)/0.7))
        ba = alpha_t(f, 29.0, 9.0)
        if bsc > 0.05 and ba > 0.05:
            img = blend(img, ov)
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            draw_speech_bubble(d, W-210, H//2-100, 340, 180,
                               ["Talk to your", "daughters."],
                               font("round", 40), bsc * ba)

        if alpha_t(f, 31.5, 6.5) > 0.05:
            text_center(d, "WITHOUT FEAR.", W//2, H//2+80, font("serif", 54), DARK_BROWN)
        if alpha_t(f, 32.5, 5.5) > 0.05:
            text_center(d, "WITHOUT SHAME.", W//2, H//2+155, font("serif", 54), DEEP_ROSE)
        if alpha_t(f, 33.5, 4.5) > 0.05:
            text_center(d, "Teach them.", W//2, H//2+240, font("sans", 42), NUDE_BROWN)

    # ── DIGNITY 38–48s ────────────────────────────────────────────────────────
    elif 38 <= t < 48:
        st = t - 38
        if alpha_t(f, 38.2, 9.8) > 0.05:
            fn_l = font("serif", 52)
            text_center(d, "Not LUXURY.", W//2, H//2-250, fn_l, NUDE_BROWN)
            cp = clamp((t-38.7)/0.5)
            if cp > 0:
                bb = fn_l.getbbox("Not LUXURY.")
                lw = bb[2]-bb[0]
                d.line([(W//2-lw//2, H//2-250), (W//2-lw//2+int(lw*cp), H//2-250)],
                       fill=rgba(DEEP_ROSE, 230), width=5)

        diga = alpha_t(f, 39.2, 8.8)
        if diga > 0.05:
            dsc = ease_bounce(clamp((t-39.2)/0.7))
            fn_d = font("serif", int(100*dsc))
            if dsc > 0.05:
                img = blend(img, ov)
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                d = ImageDraw.Draw(ov)
                img = glow_text(img.convert("RGBA"), "DIGNITY", W//2, H//2-80, fn_d, DEEP_ROSE, LILAC, 30)
                d = ImageDraw.Draw(ov)
                text_center(d, "👑", W//2+250, H//2-130, font("round", int(60*dsc)), WARM_AMBER)

        # Floating dignity words
        fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fld = ImageDraw.Draw(fl)
        words = [("dignity",LILAC,60,0.25,0.0),("health",SOFT_PINK,46,0.75,1.5),
                 ("care",NUDE_BROWN,38,0.15,0.8),("confidence",LILAC,40,0.80,2.5),
                 ("support",SOFT_PINK,36,0.45,3.2),("strength",WARM_AMBER,34,0.60,1.0)]
        for word,col,sz,xf,delay in words:
            wt = st - delay
            if wt < 0: continue
            fn_fw = font("serif", sz)
            phase = (wt % 6.0) / 6.0
            wx_ = int(xf * W)
            wy_ = int(H * 0.92 - phase * H * 1.05)
            if -80 < wy_ < H+60:
                wa = int(160 * math.sin(math.pi * phase))
                bb = fn_fw.getbbox(word)
                fld.text((wx_ - (bb[2]-bb[0])//2, wy_), word, font=fn_fw, fill=rgba(col, wa))
        img = blend(img, fl)
        d = ImageDraw.Draw(ov)

        if alpha_t(f, 41.0, 7.0) > 0.05:
            text_center(d, "Menstrual hygiene is", W//2, H//2+320, font("sans", 40), NUDE_BROWN)
            text_center(d, "every girl's right.", W//2, H//2+375, font("sans", 40), NUDE_BROWN)
        if alpha_t(f, 43.0, 5.0) > 0.05:
            text_center(d, "Health without the complexity.", W//2, H//2+450, font("serif", 42), DEEP_ROSE)

    # ── CTA SCREEN 48–60s ─────────────────────────────────────────────────────
    elif t >= 48:
        st = t - 48
        # Fade in gradient overlay
        fade_a = int(240 * min(st / 1.5, 1.0))
        bg_a = int(200 * min(st / 1.5, 1.0))
        d.rectangle([0, 0, W, H], fill=(*BEIGE, bg_a))

        la = ease_out(anim_t(f, 48.5, 1.0))
        if la > 0.05:
            lp = 1.3 * la * (1.0 + 0.03 * math.sin(st * 2))
            draw_logo(d, W//2, 300, scale=lp, alpha=int(240*la))

        ta_ = ease_out(anim_t(f, 49.5, 1.2))
        if ta_ > 0.05:
            text_center(d, "🌸 HAPPY", W//2, 520, font("round", 38), DEEP_ROSE)
            text_center(d, "WORLD MENSTRUAL", W//2, 590, font("serif", 62), NUDE_BROWN)
            text_center(d, "HYGIENE DAY 🌸", W//2, 660, font("serif", 62), NUDE_BROWN)

        da_ = ease_out(anim_t(f, 50.2, 0.8))
        if da_ > 0.05:
            d.rounded_rectangle([W//2-100, 700, W//2+100, 760], radius=30,
                                 fill=rgba(DEEP_ROSE, int(220*da_)))
            text_center(d, "May 28", W//2, 730, font("sans", 36), CREAM)

        fa_ = ease_out(anim_t(f, 51.0, 1.0))
        if fa_ > 0.05:
            d.rounded_rectangle([W//2-280, 830, W//2+280, 1010], radius=24,
                                 fill=rgba(CREAM, int(240*fa_)), outline=rgba(SOFT_PINK, int(220*fa_)), width=4)
            text_center(d, "Follow for more", W//2, 880, font("round", 36), DARK_BROWN)
            text_center(d, "health without the complexity", W//2, 940, font("round", 32), NUDE_BROWN)

        ha_ = ease_out(anim_t(f, 52.0, 0.8))
        if ha_ > 0.05:
            fn_h = font("sans", 42)
            chars = "@DrPsCorner"
            vis = max(1, int(len(chars) * min((st-4.0)/1.5, 1.0)))
            ht = "📱 " + chars[:vis]
            text_center(d, ht, W//2, 1070, fn_h, DEEP_ROSE)

        # Petal rain
        pl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pd_ = ImageDraw.Draw(pl)
        rng = np.random.default_rng(int(st * 20))
        for _ in range(20):
            px_ = int(rng.uniform(0, W))
            py_ = int((rng.uniform(0, 1.0)*H + st*120) % (H+40)) - 20
            pr_ = int(rng.uniform(8, 22))
            pc_ = tuple(rng.choice([list(SOFT_PINK), list(LILAC)]).tolist())
            pang = rng.uniform(0, 2*math.pi)
            pts = [(px_ + int(math.cos(pang+j*math.pi/4)*pr_),
                    py_ + int(math.sin(pang+j*math.pi/4)*pr_*0.5)) for j in range(8)]
            if len(pts) >= 3:
                pd_.polygon(pts, fill=rgba(pc_, 120))
        img = blend(img, pl)
        d = ImageDraw.Draw(ov)

        if alpha_t(f, 53.0, 7.0) > 0.05:
            ba_ = ease_out(anim_t(f, 53.0, 1.0))
            d.line([(W//4, 1140), (3*W//4, 1140)], fill=rgba(NUDE_BROWN, int(120*ba_)), width=2)
            text_center(d, "🌺 DR. P'S CORNER 🌺", W//2, 1190, font("round", 40), NUDE_BROWN)
            draw_hibiscus(d, W//2-320, 1190, 28, ba_, SOFT_PINK)
            draw_hibiscus(d, W//2+320, 1190, 28, ba_, LILAC)

        if alpha_t(f, 54.5, 5.5) > 0.05:
            text_center(d, "Health. Dignity. Care.", W//2, 1270, font("serif", 46), DEEP_ROSE)

    img = blend(img, ov)
    return img.convert("RGB")

# ─── WAVESPEED API ────────────────────────────────────────────────────────────
def ws_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

def image_to_b64(path: str) -> str:
    ext = Path(path).suffix.lstrip(".").lower()
    mime = "jpeg" if ext in ("jpg", "jpeg") else "png"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/{mime};base64,{data}"

def submit_i2v(api_key: str, image_path: str, prompt: str, duration_sec: int) -> str:
    """Submit image-to-video task. Returns task ID."""
    num_frames = max(16, min(81, duration_sec * 16))
    payload = {
        "image": image_to_b64(image_path),
        "prompt": prompt,
        "num_frames": num_frames,
        "guidance_scale": 6.0,
        "num_inference_steps": 30,
    }
    r = requests.post(
        f"{WAVESPEED_BASE}/wavespeed-ai/wan-2.1/i2v-480p",
        headers=ws_headers(api_key),
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["data"]["id"]

def submit_t2v(api_key: str, prompt: str, duration_sec: int) -> str:
    """Submit text-to-video task. Returns task ID."""
    num_frames = max(16, min(81, duration_sec * 16))
    payload = {
        "prompt": prompt,
        "num_frames": num_frames,
        "guidance_scale": 6.0,
        "num_inference_steps": 30,
        "size": "480*832",
    }
    r = requests.post(
        f"{WAVESPEED_BASE}/wavespeed-ai/wan-2.1/t2v-480p",
        headers=ws_headers(api_key),
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["data"]["id"]

def poll_task(api_key: str, task_id: str, timeout: int = 600) -> str:
    """Poll until complete; return output URL."""
    deadline = time.time() + timeout
    interval = 3
    while time.time() < deadline:
        r = requests.get(
            f"{WAVESPEED_BASE}/predictions/{task_id}/result",
            headers=ws_headers(api_key),
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()["data"]
        status = data.get("status", "")
        if status == "completed":
            outputs = data.get("outputs", [])
            if outputs:
                return outputs[0]
            raise RuntimeError("Task completed but no outputs returned")
        if status in ("failed", "cancelled"):
            raise RuntimeError(f"Task {status}: {data.get('error', 'unknown error')}")
        print(f"    task {task_id[:12]}… status={status}", flush=True)
        time.sleep(interval)
        interval = min(interval * 1.3, 10)
    raise TimeoutError(f"Task {task_id} timed out after {timeout}s")

def download_video(url: str, dest: Path) -> Path:
    print(f"  Downloading {url[:60]}…", flush=True)
    urllib.request.urlretrieve(url, dest)
    return dest

# ─── CLIP BUILDER ─────────────────────────────────────────────────────────────
def frames_from_video(path: Path, target_w: int = W, target_h: int = H) -> list:
    """Load a video file and return a list of PIL RGB frames scaled to target size."""
    import imageio
    reader = imageio.get_reader(str(path))
    frames = []
    for raw in reader:
        img = Image.fromarray(raw).convert("RGB")
        # Scale to fill then center-crop
        iw, ih = img.size
        scale = max(target_w / iw, target_h / ih)
        nw, nh = int(iw * scale), int(ih * scale)
        img = img.resize((nw, nh), Image.LANCZOS)
        ox, oy = (nw - target_w) // 2, (nh - target_h) // 2
        img = img.crop((ox, oy, ox + target_w, oy + target_h))
        frames.append(img)
    reader.close()
    return frames

def extend_frames(frames: list, target_count: int) -> list:
    """Loop or trim frames to reach exactly target_count."""
    if not frames:
        raise ValueError("No frames provided")
    result = []
    while len(result) < target_count:
        result.extend(frames)
    return result[:target_count]

def fallback_bg(color_top, color_bot, count: int) -> list:
    """Generate plain gradient frames when no video is available."""
    frame = Image.new("RGB", (W, H))
    arr = np.array(frame)
    for y in range(H):
        t = y / H
        arr[y, :, 0] = int(color_top[0]*(1-t) + color_bot[0]*t)
        arr[y, :, 1] = int(color_top[1]*(1-t) + color_bot[1]*t)
        arr[y, :, 2] = int(color_top[2]*(1-t) + color_bot[2]*t)
    base = Image.fromarray(arr)
    return [base.copy() for _ in range(count)]

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Dr. P WaveSpeed video generator")
    parser.add_argument("--image", default=None,
                        help="Path to Dr. P base image (enables I2V mode)")
    parser.add_argument("--output", default=str(ASSETS_DIR / "drp_wavespeed.mp4"),
                        help="Output video path")
    parser.add_argument("--api-key", default=None,
                        help="WaveSpeed API key (or set WAVESPEED_API_KEY env var)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip WaveSpeed calls; use gradient fallback backgrounds")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("WAVESPEED_API_KEY", "")
    if not api_key and not args.dry_run:
        sys.exit("Error: provide --api-key or set WAVESPEED_API_KEY env var")

    use_i2v = bool(args.image and os.path.exists(str(args.image)))
    mode = "I2V" if use_i2v else "T2V"
    print(f"Mode: {'dry-run' if args.dry_run else mode}")
    print(f"Output: {args.output}\n")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        all_bg_frames: list = []

        for scene_idx, (start_s, end_s, i2v_prompt, t2v_prompt) in enumerate(SCENES):
            duration = end_s - start_s
            frame_count = duration * FPS
            print(f"Scene {scene_idx+1}/{len(SCENES)}  [{start_s}s–{end_s}s]  ({duration}s → {frame_count} frames)")

            if args.dry_run:
                colors = [BEIGE, LILAC, SOFT_PINK, LILAC, BEIGE, DEEP_ROSE, LILAC, CREAM]
                bg_frames = fallback_bg(colors[scene_idx % len(colors)], BEIGE, frame_count)
            else:
                try:
                    prompt = i2v_prompt if use_i2v else t2v_prompt
                    print(f"  Submitting to WaveSpeed ({mode})…")
                    if use_i2v:
                        task_id = submit_i2v(api_key, args.image, prompt, duration)
                    else:
                        task_id = submit_t2v(api_key, t2v_prompt, duration)
                    print(f"  Task ID: {task_id}")
                    output_url = poll_task(api_key, task_id)
                    clip_path = tmp / f"scene_{scene_idx:02d}.mp4"
                    download_video(output_url, clip_path)
                    raw_frames = frames_from_video(clip_path)
                    bg_frames = extend_frames(raw_frames, frame_count)
                    print(f"  ✓ {len(bg_frames)} background frames ready")
                except Exception as exc:
                    print(f"  ⚠ WaveSpeed error: {exc}  — using gradient fallback", flush=True)
                    bg_frames = fallback_bg(LILAC, BEIGE, frame_count)

            # Composite overlays
            global_f_start = start_s * FPS
            composited = []
            for i, bg in enumerate(bg_frames):
                global_f = global_f_start + i
                composited.append(composite_overlay(bg, global_f))
            all_bg_frames.extend(composited)
            print(f"  ✓ Composited {len(composited)} frames")

        # Write final video
        print(f"\nEncoding {len(all_bg_frames)} total frames → {args.output}")
        import imageio
        import imageio_ffmpeg
        os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
        writer = imageio.get_writer(
            args.output,
            fps=FPS,
            codec="libx264",
            quality=8,
            ffmpeg_params=["-preset", "fast", "-pix_fmt", "yuv420p",
                           "-crf", "20", "-movflags", "+faststart"],
            macro_block_size=1,
        )
        for frame in all_bg_frames:
            writer.append_data(np.array(frame))
        writer.close()

        size_mb = os.path.getsize(args.output) / 1024 / 1024
        print(f"\nDone! {args.output} ({size_mb:.1f} MB)")
        print("\nTo run with your Dr. P image:")
        print(f"  WAVESPEED_API_KEY=<key> python generate_wavespeed.py --image /path/to/drp.png")


if __name__ == "__main__":
    main()
