"""
Dr. P's Corner — World Menstrual Hygiene Day
Motion Graphics Video Generator
9:16 | 1080x1920 | 30fps | ~60 seconds
"""

import math
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
W, H = 1080, 1920
FPS = 30
DURATION = 60
TOTAL_FRAMES = DURATION * FPS

ASSETS_DIR = "/home/user/ass"
DR_P_IMAGE = "/root/.claude/uploads/ddbf9471-7d02-4e3c-a58c-bbdf2f902fb5/fa8c6091-file_000000006034720aadb8f4d7add6cb1a.png"
OUTPUT_VIDEO = os.path.join(ASSETS_DIR, "drp_menstrual_hygiene_day.mp4")

FONT_SERIF = "/root/.fonts/PlayfairDisplay-Bold.ttf"
FONT_SANS  = "/root/.fonts/DMSans-Medium.ttf"
FONT_ROUND = "/root/.fonts/Nunito-SemiBold.ttf"

# ─── BRAND PALETTE ────────────────────────────────────────────────────────────
BEIGE       = (245, 237, 224)
SOFT_PINK   = (242, 184, 198)
LILAC       = (200, 180, 226)
NUDE_BROWN  = (160, 120, 90)
CREAM       = (255, 248, 242)
DEEP_ROSE   = (212, 96, 122)
WARM_AMBER  = (230, 180, 130)
DARK_BROWN  = (100, 65, 45)
WHITE       = (255, 255, 255)

# ─── FONT HELPERS ─────────────────────────────────────────────────────────────
def font(kind, size):
    path = {"serif": FONT_SERIF, "sans": FONT_SANS, "round": FONT_ROUND}[kind]
    return ImageFont.truetype(path, size)

# ─── EASING ───────────────────────────────────────────────────────────────────
def ease_out(t):
    return 1 - (1 - t) ** 3

def ease_in_out(t):
    return 3*t**2 - 2*t**3

def ease_bounce(t):
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

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

def anim_t(frame, start_sec, duration_sec):
    """Return 0..1 animation progress."""
    t = (frame / FPS - start_sec) / duration_sec
    return clamp(t)

def alpha_t(frame, in_sec, out_sec, fade=0.3):
    """Return 0..1 alpha with fade-in and fade-out."""
    total = out_sec - in_sec
    t = frame / FPS - in_sec
    if t < 0:
        return 0.0
    if t < fade:
        return ease_out(t / fade)
    if t > total - fade:
        return ease_out((total - t) / fade)
    if t > total:
        return 0.0
    return 1.0

# ─── DRAWING UTILITIES ────────────────────────────────────────────────────────
def rgba(color, a=255):
    if len(color) == 3:
        return (*color, a)
    return color

def blend_overlay(base, overlay_img):
    """Alpha-composite overlay_img (RGBA) onto base (RGB or RGBA)."""
    if base.mode != "RGBA":
        base = base.convert("RGBA")
    return Image.alpha_composite(base, overlay_img)

def draw_rounded_rect(draw, xy, radius, fill, outline=None, outline_width=3):
    x1, y1, x2, y2 = xy
    fill_rgba = rgba(fill) if len(fill) == 3 else fill
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill_rgba,
                            outline=rgba(outline) if outline else None,
                            width=outline_width)

def draw_text_centered(draw, text, cx, cy, fnt, color, shadow=True):
    bbox = fnt.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = cx - tw // 2
    y = cy - th // 2
    if shadow:
        draw.text((x+3, y+3), text, font=fnt, fill=rgba(DARK_BROWN, 60))
    draw.text((x, y), text, font=fnt, fill=rgba(color))

def draw_text_left(draw, text, lx, cy, fnt, color):
    bbox = fnt.getbbox(text)
    th = bbox[3] - bbox[1]
    draw.text((lx, cy - th // 2), text, font=fnt, fill=rgba(color))

def glow_circle(img, cx, cy, radius, color, alpha=80):
    """Add a soft radial glow."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for r in range(radius, 0, -max(1, radius // 12)):
        a = int(alpha * (1 - r / radius) ** 2)
        d = ImageDraw.Draw(layer)
        d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(*color[:3], a))
    return Image.alpha_composite(img if img.mode=="RGBA" else img.convert("RGBA"), layer)

def draw_glow_text(draw, img, text, cx, cy, fnt, color, glow_color=None, glow_r=20):
    """Draw text with a glow halo."""
    glow_color = glow_color or color
    bbox = fnt.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = cx - tw // 2
    y = cy - th // 2
    # glow layer
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for offset in range(glow_r, 0, -2):
        a = int(120 * (1 - offset / glow_r) ** 2)
        gd.text((x, y), text, font=fnt, fill=(*glow_color[:3], a))
    glow = glow.filter(ImageFilter.GaussianBlur(glow_r // 3))
    img_rgba = img if img.mode == "RGBA" else img.convert("RGBA")
    img_rgba = Image.alpha_composite(img_rgba, glow)
    draw2 = ImageDraw.Draw(img_rgba)
    draw2.text((x+2, y+2), text, font=fnt, fill=rgba(DARK_BROWN, 80))
    draw2.text((x, y), text, font=fnt, fill=rgba(color))
    return img_rgba

def draw_gradient_bg(img, top_color, bottom_color):
    """Fill the image with a vertical gradient."""
    arr = np.array(img)
    for y in range(H):
        t = y / H
        r = int(top_color[0] * (1-t) + bottom_color[0] * t)
        g = int(top_color[1] * (1-t) + bottom_color[1] * t)
        b = int(top_color[2] * (1-t) + bottom_color[2] * t)
        arr[y, :, :3] = [r, g, b]
    return Image.fromarray(arr)

def lerp_color(c1, c2, t):
    return tuple(int(c1[i]*(1-t) + c2[i]*t) for i in range(3))

def draw_bokeh(draw, seed, count=18, alpha=40):
    """Floating soft bokeh circles."""
    rng = np.random.default_rng(seed)
    for _ in range(count):
        x = int(rng.uniform(0, W))
        y = int(rng.uniform(0, H))
        r = int(rng.uniform(20, 120))
        col = rng.choice([SOFT_PINK, LILAC, WARM_AMBER, BEIGE])
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(*col[:3], alpha))

# ─── ICON DRAWING ─────────────────────────────────────────────────────────────
def draw_pad_icon(draw, cx, cy, size, progress=1.0, color=SOFT_PINK, outline=NUDE_BROWN):
    """Animated sanitary pad icon."""
    w = int(size * 0.6 * progress)
    h = int(size * progress)
    r = min(w, h) // 3
    if w < 4 or h < 4:
        return
    # body
    draw.rounded_rectangle([cx-w//2, cy-h//2, cx+w//2, cy+h//2],
                            radius=r, fill=rgba(color, 220), outline=rgba(outline, 200), width=3)
    # wings
    wing_w = int(w * 0.35 * progress)
    wing_h = int(h * 0.4 * progress)
    if wing_w > 2 and wing_h > 2:
        draw.rounded_rectangle([cx-w//2-wing_w, cy-wing_h//2, cx-w//2+4, cy+wing_h//2],
                                radius=4, fill=rgba(color, 160), outline=rgba(outline, 160), width=2)
        draw.rounded_rectangle([cx+w//2-4, cy-wing_h//2, cx+w//2+wing_w, cy+wing_h//2],
                                radius=4, fill=rgba(color, 160), outline=rgba(outline, 160), width=2)
    # center stripe
    stripe_h = int(h * 0.5 * progress)
    if stripe_h > 2:
        draw.rounded_rectangle([cx-4, cy-stripe_h//2, cx+4, cy+stripe_h//2],
                                radius=2, fill=rgba(outline, 120))

def draw_calendar_icon(draw, cx, cy, size, flip_progress=0.0, color=LILAC, outline=NUDE_BROWN):
    """Calendar icon with optional page-flip progress."""
    s = int(size * 0.9)
    draw.rounded_rectangle([cx-s//2, cy-s//2, cx+s//2, cy+s//2],
                            radius=8, fill=rgba(CREAM, 230), outline=rgba(outline, 220), width=3)
    # header
    draw.rounded_rectangle([cx-s//2, cy-s//2, cx+s//2, cy-s//4],
                            radius=8, fill=rgba(color, 220))
    # grid lines
    cols, rows = 7, 5
    cw = s // cols
    rh = int(s * 0.6 / rows)
    gx = cx - s//2 + 2
    gy = cy - s//4 + 4
    for r in range(rows):
        for c in range(cols):
            dot_x = gx + c*cw + cw//2
            dot_y = gy + r*rh + rh//2
            dot_r = 4
            is_highlighted = (r == int(flip_progress * rows) and c == 2)
            col = DEEP_ROSE if is_highlighted else (outline if (r+c) % 3 == 0 else BEIGE)
            draw.ellipse([dot_x-dot_r, dot_y-dot_r, dot_x+dot_r, dot_y+dot_r],
                         fill=rgba(col, 200 if is_highlighted else 120))

def draw_drop_icon(draw, cx, cy, size, pulse_or_color=1.0, color=DEEP_ROSE):
    # Handle old call signature: draw_drop_icon(draw, cx, cy, size, color_tuple)
    if isinstance(pulse_or_color, tuple):
        color = pulse_or_color
        pulse = 1.0
    else:
        pulse = pulse_or_color
    s = int(size * pulse)
    if s < 4:
        return
    pts = []
    # teardrop shape
    for i in range(20):
        angle = math.pi * 2 * i / 20
        if angle < math.pi:
            rx = s * 0.45 * math.sin(angle)
            ry = -s * 0.5 * math.cos(angle)
        else:
            rx = s * 0.35 * math.sin(angle)
            ry = -s * 0.5 * math.cos(angle)
        pts.append((cx + int(rx), cy + int(ry)))
    draw.polygon(pts, fill=rgba(color, 200), outline=rgba(DARK_BROWN, 120))

def draw_hibiscus(draw, cx, cy, size, unfurl=1.0, color=LILAC):
    """5-petal hibiscus flower."""
    petals = 5
    petal_len = int(size * 0.5 * unfurl)
    petal_w = int(size * 0.22 * unfurl)
    if petal_len < 3:
        return
    for i in range(petals):
        angle = math.pi * 2 * i / petals - math.pi / 2
        px = cx + int(math.cos(angle) * petal_len * 0.6)
        py = cy + int(math.sin(angle) * petal_len * 0.6)
        pts = []
        for j in range(16):
            a = angle + math.pi * 2 * j / 16
            ex = px + int(math.cos(a) * petal_w)
            ey = py + int(math.sin(a) * petal_len * 0.5)
            pts.append((ex, ey))
        if len(pts) >= 3:
            draw.polygon(pts, fill=rgba(color, 200), outline=rgba(NUDE_BROWN, 120))
    # center
    draw.ellipse([cx-size//6, cy-size//6, cx+size//6, cy+size//6],
                 fill=rgba(SOFT_PINK, 240), outline=rgba(NUDE_BROWN, 180))

def draw_heart(draw, cx, cy, size, color=DEEP_ROSE, alpha=220, progress=1.0):
    """Draw a heart shape."""
    s = int(size * progress)
    if s < 4:
        return
    pts = []
    steps = 60
    for i in range(steps):
        t = math.pi * 2 * i / steps
        x = int(s * 0.85 * math.sin(t)**3)
        y = int(-s * (0.8*math.cos(t) - 0.31*math.cos(2*t) - 0.12*math.cos(3*t) - 0.04*math.cos(4*t)))
        pts.append((cx + x, cy + y))
    if len(pts) >= 3:
        draw.polygon(pts, fill=rgba(color, alpha))

def draw_sparkle(draw, cx, cy, size, color=SOFT_PINK, alpha=200):
    """4-point star sparkle."""
    for angle in [0, math.pi/2, math.pi, 3*math.pi/2]:
        ex = cx + int(math.cos(angle) * size)
        ey = cy + int(math.sin(angle) * size)
        draw.line([cx, cy, ex, ey], fill=rgba(color, alpha), width=3)
    for angle in [math.pi/4, 3*math.pi/4, 5*math.pi/4, 7*math.pi/4]:
        ex = cx + int(math.cos(angle) * size * 0.6)
        ey = cy + int(math.sin(angle) * size * 0.6)
        draw.line([cx, cy, ex, ey], fill=rgba(color, alpha), width=2)

# ─── SILHOUETTE HELPERS ───────────────────────────────────────────────────────
def draw_person_silhouette(draw, cx, base_y, scale=1.0, color=LILAC, alpha=160, is_child=False):
    """Simple person silhouette (head + body)."""
    s = scale
    head_r = int(28 * s)
    body_h = int(70 * s)
    shoulder_w = int(40 * s) if not is_child else int(30 * s)
    leg_h = int(50 * s)
    hip_w = int(35 * s) if not is_child else int(25 * s)
    # head
    hy = base_y - leg_h - body_h - head_r
    draw.ellipse([cx-head_r, hy-head_r, cx+head_r, hy+head_r], fill=rgba(color, alpha))
    # body
    body_top = hy + head_r
    body_pts = [
        (cx - shoulder_w, body_top + 5),
        (cx + shoulder_w, body_top + 5),
        (cx + hip_w, body_top + body_h),
        (cx - hip_w, body_top + body_h),
    ]
    draw.polygon(body_pts, fill=rgba(color, alpha))
    # legs
    draw.line([cx - hip_w//2, base_y - leg_h, cx - hip_w//4, base_y], fill=rgba(color, alpha), width=int(14*s))
    draw.line([cx + hip_w//2, base_y - leg_h, cx + hip_w//4, base_y], fill=rgba(color, alpha), width=int(14*s))

def draw_schoolgirl_silhouette(draw, cx, base_y, scale=1.0, color=LILAC, alpha=160, hide_pose=0.0):
    """Schoolgirl with backpack and hiding pose."""
    s = scale
    draw_person_silhouette(draw, cx, base_y, scale, color, alpha, is_child=True)
    # backpack
    bp_x = cx + int(25*s)
    bp_y = base_y - int(90*s)
    bp_w = int(20*s)
    bp_h = int(35*s)
    draw.rounded_rectangle([bp_x, bp_y-bp_h//2, bp_x+bp_w, bp_y+bp_h//2],
                            radius=5, fill=rgba(NUDE_BROWN, int(130 + 40*hide_pose)))
    # hiding arm
    if hide_pose > 0.1:
        arm_x = cx - int(30*s)
        arm_y = base_y - int(80*s)
        draw.ellipse([arm_x - int(12*s*hide_pose), arm_y - int(10*s),
                      arm_x + int(12*s*hide_pose), arm_y + int(10*s)],
                     fill=rgba(SOFT_PINK, int(180*hide_pose)))

def draw_mother_daughter(draw, cx, base_y, scale=1.0, color=LILAC, alpha=150, bond=1.0):
    """Mother and daughter side by side."""
    # mother (right, larger)
    mx = cx + int(40 * scale)
    draw_person_silhouette(draw, mx, base_y, scale * 1.1, color, alpha)
    # daughter (left, smaller)
    dx = cx - int(25 * scale)
    draw_person_silhouette(draw, dx, base_y, scale * 0.75, SOFT_PINK, alpha, is_child=True)
    # connecting arm/bond
    if bond > 0.1:
        arm_y = base_y - int(90 * scale)
        draw.line([dx + int(20*scale), arm_y, mx - int(30*scale), arm_y - int(5*scale)],
                  fill=rgba(WARM_AMBER, int(160*bond)), width=int(8*scale))

# ─── SPEECH BUBBLE ────────────────────────────────────────────────────────────
def draw_speech_bubble(draw, cx, cy, w, h, text_lines, fnt, text_color, scale=1.0, tail_side="left"):
    sw = int(w * scale)
    sh = int(h * scale)
    if sw < 20 or sh < 20:
        return
    # bubble body
    draw.rounded_rectangle([cx-sw//2, cy-sh//2, cx+sw//2, cy+sh//2],
                            radius=20, fill=rgba(CREAM, 240), outline=rgba(SOFT_PINK, 220), width=4)
    # tail
    if tail_side == "left":
        tail_pts = [(cx-sw//2+10, cy+sh//4), (cx-sw//2-20, cy+sh//2+15), (cx-sw//2+30, cy+sh//2-5)]
    else:
        tail_pts = [(cx+sw//2-10, cy+sh//4), (cx+sw//2+20, cy+sh//2+15), (cx+sw//2-30, cy+sh//2-5)]
    draw.polygon(tail_pts, fill=rgba(CREAM, 240))
    draw.polygon(tail_pts, outline=rgba(SOFT_PINK, 220))
    # text
    line_h = fnt.getbbox("A")[3] + 8
    total_h = len(text_lines) * line_h
    start_y = cy - total_h // 2
    for i, line in enumerate(text_lines):
        bbox = fnt.getbbox(line)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw//2, start_y + i*line_h), line, font=fnt, fill=rgba(text_color))

# ─── DR. P BASE IMAGE ─────────────────────────────────────────────────────────
def prepare_dr_p_base():
    """Load and crop Dr. P image to fill 9:16 frame."""
    img = Image.open(DR_P_IMAGE).convert("RGB")
    iw, ih = img.size

    # Scale to fill 9:16
    scale = max(W / iw, H / ih)
    nw = int(iw * scale)
    nh = int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)

    # Center crop
    left = (nw - W) // 2
    top = (nh - H) // 2
    img = img.crop((left, top, left + W, top + H))

    # Add warm overlay to match brand palette
    overlay = Image.new("RGBA", (W, H), (*BEIGE, 60))
    base = img.convert("RGBA")
    return Image.alpha_composite(base, overlay).convert("RGB")

DR_P_BASE = None

def get_dr_p(zoom=1.0):
    global DR_P_BASE
    if DR_P_BASE is None:
        DR_P_BASE = prepare_dr_p_base()
    if abs(zoom - 1.0) < 0.001:
        return DR_P_BASE.copy()
    # Apply zoom centered
    zw = int(W / zoom)
    zh = int(H / zoom)
    ox = (W - zw) // 2
    oy = (H - zh) // 2
    cropped = DR_P_BASE.crop((ox, oy, ox+zw, oy+zh))
    return cropped.resize((W, H), Image.LANCZOS)

# ─── POPUP CARD ───────────────────────────────────────────────────────────────
def draw_popup_card(img, text, cx, cy, progress, color=NUDE_BROWN, bg=CREAM, border=SOFT_PINK, strike=False):
    if progress <= 0:
        return img
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    d = ImageDraw.Draw(overlay)
    fnt = font("sans", 42)
    bbox = fnt.getbbox(text)
    tw = bbox[2] - bbox[0] + 60
    th = bbox[3] - bbox[1] + 36
    sw = int(tw * progress)
    sh = int(th * progress)
    if sw < 10 or sh < 10:
        return img
    alpha = int(240 * min(progress * 3, 1.0))
    d.rounded_rectangle([cx-sw//2, cy-sh//2, cx+sw//2, cy+sh//2],
                         radius=20, fill=rgba(bg, alpha), outline=rgba(border, alpha), width=4)
    if progress > 0.6:
        text_alpha = int(255 * ((progress - 0.6) / 0.4))
        d.text((cx - (bbox[2]-bbox[0])//2, cy - (bbox[3]-bbox[1])//2),
               text, font=fnt, fill=rgba(color, text_alpha))
        if strike and progress > 0.8:
            sa = int(255 * ((progress - 0.8) / 0.2))
            lx1 = cx - tw//2 + 20
            lx2 = cx + tw//2 - 20
            d.line([(lx1, cy+2), (lx2, cy+2)], fill=rgba(DEEP_ROSE, sa), width=4)
    base = img if img.mode=="RGBA" else img.convert("RGBA")
    return Image.alpha_composite(base, overlay)

# ─── FLOATING WORDS ───────────────────────────────────────────────────────────
FLOAT_WORDS = [
    ("DIGNITY", LILAC, 68, 0.3),
    ("HEALTH", SOFT_PINK, 52, 0.5),
    ("CARE", NUDE_BROWN, 44, 0.7),
    ("CONFIDENCE", LILAC, 46, 0.4),
    ("SUPPORT", SOFT_PINK, 40, 0.6),
    ("GRACE", WARM_AMBER, 36, 0.8),
    ("STRENGTH", NUDE_BROWN, 38, 0.3),
]

def draw_float_words(draw, frame_in_scene, total_duration, words=FLOAT_WORDS):
    """Words floating upward across the scene."""
    for i, (word, color, sz, x_frac) in enumerate(words):
        fnt = font("serif", sz)
        start_offset = i * 1.2
        t = (frame_in_scene / FPS) - start_offset
        if t < 0:
            continue
        cycle = 4.0
        phase = (t % cycle) / cycle
        cx = int(x_frac * W)
        cy = int(H * 0.95 - phase * H * 1.1)
        if cy < -80 or cy > H + 60:
            continue
        alpha = int(180 * math.sin(math.pi * phase))
        d_layer = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bbox = fnt.getbbox(word)
        tw = bbox[2] - bbox[0]
        layer = Image.new("RGBA", (W, H), (0,0,0,0))
        ld = ImageDraw.Draw(layer)
        ld.text((cx - tw//2, cy), word, font=fnt, fill=rgba(color, alpha))
        draw._image = Image.alpha_composite(
            draw._image if hasattr(draw, '_image') else layer,
            layer
        )

# ─── DR. P'S CORNER LOGO TEXT ─────────────────────────────────────────────────
def draw_logo(draw, cx, cy, scale=1.0, alpha=220):
    fnt1 = font("serif", int(44 * scale))
    fnt2 = font("serif", int(28 * scale))
    draw.text((cx - fnt1.getbbox("Dr. P's")[2]//2, cy - int(30*scale)),
              "Dr. P's", font=fnt1, fill=rgba(NUDE_BROWN, alpha))
    draw.text((cx - fnt2.getbbox("CORNER")[2]//2, cy + int(20*scale)),
              "CORNER", font=fnt2, fill=rgba(DEEP_ROSE, alpha))
    heart_size = int(10 * scale)
    hx = cx
    hy = cy + int(58*scale)
    draw_heart(draw, hx, hy, heart_size, DEEP_ROSE, alpha)

# ─── SCENE BUILDERS ───────────────────────────────────────────────────────────
def build_frame(f):
    """Build one frame at index f."""
    t = f / FPS  # time in seconds

    # Zoom progression
    if t < 3:
        zoom = 1.0
    elif t < 16:
        zoom = 1.0 + 0.03 * ((t - 3) / 13)
    elif t < 21:
        zoom = 1.03 + 0.03 * ((t - 16) / 5)
    elif t < 28:
        zoom = 1.06 + 0.04 * ((t - 21) / 7)
    elif t < 38:
        zoom = 1.10 - 0.04 * ((t - 28) / 10)
    elif t < 48:
        zoom = 1.06 + 0.02 * ((t - 38) / 10)
    else:
        zoom = 1.08

    img = get_dr_p(zoom)

    # Darken for CTA section
    if t >= 48:
        dark = Image.new("RGB", (W, H), (30, 20, 15))
        blend = int(180 * min((t - 48) / 2.0, 1.0))
        img = Image.blend(img, dark, blend / 255)

    img = img.convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    d = ImageDraw.Draw(overlay)

    # ── SCENE 1: INTRO 0–3s ─────────────────────────────────────────────────
    if t < 3.5:
        # Bokeh blobs
        bokeh_layer = Image.new("RGBA", (W, H), (0,0,0,0))
        bd = ImageDraw.Draw(bokeh_layer)
        seed = int(t * 10)
        draw_bokeh(bd, seed=42, count=12, alpha=35)
        img = Image.alpha_composite(img, bokeh_layer)

        # Date card top center
        card_prog = ease_out(anim_t(f, 0.2, 0.6))
        card_alpha = int(230 * card_prog)
        if card_alpha > 10:
            cw = int(460 * card_prog)
            ch = int(110 * card_prog)
            cx_, cy_ = W//2, 180
            d.rounded_rectangle([cx_-cw//2, cy_-ch//2, cx_+cw//2, cy_+ch//2],
                                 radius=18, fill=rgba(LILAC, card_alpha), outline=rgba(NUDE_BROWN, card_alpha), width=3)
            if card_prog > 0.7:
                ta = int(255 * (card_prog - 0.7) / 0.3)
                fn1 = font("sans", 28)
                fn2 = font("serif", 44)
                draw_text_centered(d, "WORLD MENSTRUAL HYGIENE DAY", W//2, cy_-18, fn1, NUDE_BROWN, shadow=False)
                draw_text_centered(d, "May 28", W//2, cy_+28, fn2, DEEP_ROSE, shadow=False)

        # Opening text
        text_prog = alpha_t(f, 0.8, 3.5)
        if text_prog > 0.05:
            fn = font("serif", 58)
            y0 = H // 2 - 160
            slide = int((1 - ease_out(min(text_prog * 3, 1.0))) * 40)
            d.text((W//2 - fn.getbbox("Dear girls…")[2]//2, y0 + slide),
                   "Dear girls…", font=fn, fill=rgba(NUDE_BROWN, int(230*text_prog)))
            fn2 = font("serif", 48)
            d.text((W//2 - fn2.getbbox("and dear mothers…")[2]//2, y0 + 80 + slide),
                   "and dear mothers…", font=fn2, fill=rgba(DEEP_ROSE, int(200*text_prog)))

        # Logo top right
        logo_prog = ease_out(anim_t(f, 0.3, 0.8))
        if logo_prog > 0.1:
            draw_logo(d, W - 130, 120, scale=0.75 * logo_prog, alpha=int(200 * logo_prog))

    # ── SCENE 2: "NOT" STATEMENTS 3–11s ──────────────────────────────────────
    elif 3 <= t < 11:
        st = t - 3  # 0–8

        # Floating pad icon left side
        pad_prog = ease_out(anim_t(f, 3.2, 0.8))
        pad_float = int(math.sin(st * 1.5) * 12)
        draw_pad_icon(d, 130, 600 + pad_float, 90, pad_prog, SOFT_PINK, NUDE_BROWN)

        # Calendar icon right side
        cal_prog = ease_out(anim_t(f, 3.8, 0.8))
        cal_float = int(math.sin(st * 1.2 + 1) * 10)
        draw_calendar_icon(d, W - 130, 520 + cal_float, 90, st % 5 / 5, LILAC, NUDE_BROWN)

        # Hibiscus lower left
        hib_prog = ease_out(anim_t(f, 4.5, 0.8))
        hib_float = int(math.sin(st * 1.8 + 2) * 8)
        draw_hibiscus(d, 160, 900 + hib_float, 70, hib_prog, LILAC)

        # Glow pulse on background
        pulse = 0.5 + 0.5 * math.sin(st * 2)
        glow_layer = Image.new("RGBA", (W, H), (0,0,0,0))
        gd = ImageDraw.Draw(glow_layer)
        for r in range(200, 0, -20):
            a = int(15 * pulse * (1 - r/200) ** 2)
            gd.ellipse([W//2-r, H//2-r, W//2+r, H//2+r], fill=rgba(DEEP_ROSE, a))
        img = Image.alpha_composite(img, glow_layer)
        d = ImageDraw.Draw(overlay)

        # Card 1: "NOT dirty" at 3–5s
        c1p = ease_bounce(clamp((t - 3.0) / 0.5))
        c1a = alpha_t(f, 3.0, 7.5)
        img = blend_overlay(img, overlay)
        overlay = Image.new("RGBA", (W, H), (0,0,0,0))
        d = ImageDraw.Draw(overlay)
        img = draw_popup_card(img, "Periods are NOT dirty ✗", W//2, H//2 - 220,
                               c1p * c1a, DARK_BROWN, CREAM, DEEP_ROSE, strike=True)

        # Card 2: "NOT shameful" at 4.5–7s
        c2p = ease_bounce(clamp((t - 4.5) / 0.5))
        c2a = alpha_t(f, 4.5, 6.5)
        img = draw_popup_card(img, "NOT shameful ✗", W//2, H//2 - 60,
                               c2p * c2a, DARK_BROWN, CREAM, LILAC, strike=True)

        # Card 3: "NOT a punishment" at 6–9s
        c3p = ease_bounce(clamp((t - 6.0) / 0.5))
        c3a = alpha_t(f, 6.0, 5.0)
        img = draw_popup_card(img, "NOT a punishment ✗", W//2, H//2 + 100,
                               c3p * c3a, DARK_BROWN, CREAM, SOFT_PINK, strike=True)

        # Hero text bottom third
        overlay = Image.new("RGBA", (W, H), (0,0,0,0))
        d = ImageDraw.Draw(overlay)
        fn = font("serif", 52)
        fn2 = font("sans", 44)
        texts_alpha = alpha_t(f, 3.2, 7.8)
        if texts_alpha > 0.05:
            lines = [("Periods are", fn2, NUDE_BROWN),
                     ("NOT dirty.", fn, DEEP_ROSE),
                     ("NOT shameful.", fn, DEEP_ROSE),
                     ("NOT a punishment.", fn, DEEP_ROSE)]
            visible = min(4, int((t - 3.2) * 1.2) + 1)
            for i, (txt, f_, col) in enumerate(lines[:visible]):
                a = int(200 * texts_alpha)
                bbox_ = f_.getbbox(txt)
                draw_text_centered(d, txt, W//2, H - 380 + i*80, f_, col)

    # ── SCENE 3: SCHOOLGIRL / CONFIDENCE 11–16s ──────────────────────────────
    elif 11 <= t < 16:
        st = t - 11

        # Schoolgirl silhouette right side, walks in
        walk_prog = ease_out(anim_t(f, 11.0, 1.2))
        girl_x = int(W*0.75 - (1 - walk_prog) * 200)
        hide_pose = min(st * 0.4, 1.0)
        draw_schoolgirl_silhouette(d, girl_x, H - 280, scale=0.9, alpha=int(160*walk_prog), hide_pose=hide_pose)

        # Hiding pad icon near her hand
        if hide_pose > 0.3:
            pad_shiver = int(math.sin(st * 8) * 3)
            draw_pad_icon(d, girl_x - 80, H - 380, 50, hide_pose, SOFT_PINK, NUDE_BROWN)

        # Text lines
        fn = font("sans", 48)
        fn_hero = font("serif", 70)
        overlay2 = Image.new("RGBA", (W, H), (0,0,0,0))
        d2 = ImageDraw.Draw(overlay2)

        line1_a = alpha_t(f, 11.2, 4.8)
        line2_a = alpha_t(f, 12.0, 4.2)
        conf_a  = alpha_t(f, 12.8, 3.2)

        if line1_a > 0.05:
            draw_text_centered(d2, "That little girl", W//2 - 60, H//2 - 180,
                               font("sans", 44), NUDE_BROWN)
            draw_text_centered(d2, "hiding her pad in school?", W//2 - 60, H//2 - 120,
                               font("sans", 42), NUDE_BROWN)
        if line2_a > 0.05:
            draw_text_centered(d2, "She deserves…", W//2 - 60, H//2 - 40,
                               font("serif", 48), DARK_BROWN)

        # "CONFIDENCE" burst
        if conf_a > 0.05:
            conf_scale = ease_bounce(clamp((t - 12.8) / 0.6))
            img = blend_overlay(img, overlay)
            img = Image.alpha_composite(img if img.mode=="RGBA" else img.convert("RGBA"), overlay2)
            overlay2 = Image.new("RGBA", (W, H), (0,0,0,0))
            d2 = ImageDraw.Draw(overlay2)
            # Glow behind word
            glow2 = Image.new("RGBA", (W, H), (0,0,0,0))
            gd2 = ImageDraw.Draw(glow2)
            for r in range(180, 0, -15):
                a = int(60 * conf_a * (1 - r/180))
                gd2.ellipse([W//2 - 60 - r, H//2 + 50 - r//2,
                              W//2 - 60 + r, H//2 + 50 + r//2],
                             fill=rgba(LILAC, a))
            img = Image.alpha_composite(img.convert("RGBA"), glow2)
            d2 = ImageDraw.Draw(overlay2)
            fn_c = font("serif", int(80 * conf_scale))
            if conf_scale > 0.05:
                draw_text_centered(d2, "CONFIDENCE", W//2 - 60, H//2 + 60,
                                   fn_c, DEEP_ROSE)
            # Sparkles around
            if conf_a > 0.3:
                for sp_angle in range(0, 360, 45):
                    sp_x = W//2 - 60 + int(math.cos(math.radians(sp_angle)) * 160)
                    sp_y = H//2 + 60 + int(math.sin(math.radians(sp_angle)) * 80)
                    draw_sparkle(d2, sp_x, sp_y, int(18 * conf_a), LILAC, int(200*conf_a))

        overlay = Image.new("RGBA", (W, H), (0,0,0,0))
        img = blend_overlay(img, overlay2)
        d = ImageDraw.Draw(overlay)

    # ── SCENE 4: TEENAGER / SUPPORT 16–21s ───────────────────────────────────
    elif 16 <= t < 21:
        st = t - 16

        # Teen silhouette left side
        teen_prog = ease_out(anim_t(f, 16.0, 1.0))
        teen_x = int(W*0.28 + (1 - teen_prog) * 200)
        draw_person_silhouette(d, teen_x, H - 250, scale=1.0, color=LILAC,
                               alpha=int(170*teen_prog), is_child=True)

        # Stain drop icon
        if st > 0.5:
            drop_pulse = 1.0 + 0.1 * math.sin(st * 3)
            drop_a = alpha_t(f, 16.5, 4.5)
            layer_d = Image.new("RGBA", (W, H), (0,0,0,0))
            dl = ImageDraw.Draw(layer_d)
            draw_drop_icon(dl, teen_x + 40, H - 320, int(40 * drop_a * drop_pulse), DEEP_ROSE)
            img = Image.alpha_composite(img.convert("RGBA"), layer_d)
            d = ImageDraw.Draw(overlay)

        # Hands / support icon right side
        hands_prog = ease_out(anim_t(f, 16.8, 0.8))
        if hands_prog > 0.1:
            hx = W - 160
            hy = H - 400
            hw = int(80 * hands_prog)
            # Two cupped hands
            d.arc([hx-hw, hy-int(hw*0.6), hx, hy+int(hw*0.6)], 180, 360, fill=rgba(NUDE_BROWN, int(200*hands_prog)), width=6)
            d.arc([hx, hy-int(hw*0.6), hx+hw, hy+int(hw*0.6)], 180, 360, fill=rgba(NUDE_BROWN, int(200*hands_prog)), width=6)
            # Floating hearts above hands
            for i in range(3):
                heart_t = (st - i * 0.5) % 3.0
                heart_y = hy - int(heart_t * 60) - 20
                heart_a = int(180 * (1 - heart_t / 3.0) * hands_prog)
                draw_heart(d, hx + int([-25, 0, 25][i]), heart_y, 14, SOFT_PINK, heart_a)

        # Text
        fn = font("sans", 48)
        line1_a = alpha_t(f, 16.2, 4.8)
        line2_a = alpha_t(f, 17.0, 4.0)
        supp_a  = alpha_t(f, 17.8, 3.2)

        if line1_a > 0.05:
            draw_text_centered(d, "That teenager", W//2 + 40, H//2 - 180, font("sans", 44), NUDE_BROWN)
            draw_text_centered(d, "scared because of stains?", W//2 + 40, H//2 - 120, font("sans", 40), NUDE_BROWN)
        if line2_a > 0.05:
            draw_text_centered(d, "She deserves…", W//2 + 40, H//2 - 40, font("serif", 48), DARK_BROWN)

        if supp_a > 0.05:
            sup_scale = ease_bounce(clamp((t - 17.8) / 0.6))
            fn_s = font("serif", int(78 * sup_scale))
            glow3 = Image.new("RGBA", (W, H), (0,0,0,0))
            gd3 = ImageDraw.Draw(glow3)
            for r in range(160, 0, -12):
                a = int(55 * supp_a * (1 - r/160))
                gd3.ellipse([W//2 + 40 - r, H//2 + 55 - r//2,
                              W//2 + 40 + r, H//2 + 55 + r//2],
                             fill=rgba(SOFT_PINK, a))
            img = Image.alpha_composite(img.convert("RGBA"), glow3)
            overlay2b = Image.new("RGBA", (W, H), (0,0,0,0))
            d2b = ImageDraw.Draw(overlay2b)
            if sup_scale > 0.05:
                draw_text_centered(d2b, "SUPPORT", W//2 + 40, H//2 + 65, fn_s, LILAC)
                # Underline draws itself
                ul_prog = clamp((t - 18.2) / 0.5)
                if ul_prog > 0:
                    bbx = fn_s.getbbox("SUPPORT")
                    ul_w = bbx[2] - bbx[0]
                    ul_x1 = W//2 + 40 - ul_w//2
                    ul_x2 = ul_x1 + int(ul_w * ul_prog)
                    ul_y = H//2 + 65 + bbx[3]//2 + 8
                    d2b.line([(ul_x1, ul_y), (ul_x2, ul_y)], fill=rgba(DEEP_ROSE, int(220*supp_a)), width=5)
            img = Image.alpha_composite(img.convert("RGBA"), overlay2b)
            d = ImageDraw.Draw(overlay)

    # ── SCENE 5: MOTHER / CARE 21–28s ────────────────────────────────────────
    elif 21 <= t < 28:
        st = t - 21

        # Mother-daughter silhouette center-right
        md_prog = ease_out(anim_t(f, 21.0, 1.3))
        bond = min(st * 0.4, 1.0)
        md_x = int(W * 0.62)
        draw_mother_daughter(d, md_x, H - 240, scale=1.05,
                             color=LILAC, alpha=int(160*md_prog), bond=bond)

        # Heart around mother figure (draws itself)
        heart_draw_prog = clamp((t - 22.0) / 1.5)
        if heart_draw_prog > 0:
            heart_layer = Image.new("RGBA", (W, H), (0,0,0,0))
            hld = ImageDraw.Draw(heart_layer)
            for i in range(int(60 * heart_draw_prog)):
                t_h = math.pi * 2 * i / 60
                hx_i = int(70 * math.sin(t_h)**3)
                hy_i = int(-60 * (0.8*math.cos(t_h) - 0.3*math.cos(2*t_h) - 0.1*math.cos(3*t_h)))
                hld.ellipse([md_x + hx_i - 4, H - 520 + hy_i - 4,
                              md_x + hx_i + 4, H - 520 + hy_i + 4],
                             fill=rgba(LILAC, 180))
            img = Image.alpha_composite(img.convert("RGBA"), heart_layer)
            d = ImageDraw.Draw(overlay)

        # Calendar with cycling days
        cal_a = alpha_t(f, 21.5, 6.5)
        if cal_a > 0.05:
            cal_prog2 = ease_out(anim_t(f, 21.5, 0.7))
            draw_calendar_icon(d, 150, H//2 - 80, int(95*cal_prog2), st % 5 / 5, LILAC, NUDE_BROWN)
            # "every month" label
            fn_sm = font("round", 30)
            d.text((70, H//2 + 35), "every month", font=fn_sm, fill=rgba(NUDE_BROWN, int(160*cal_a)))

        # Drop pulsing
        if st > 1:
            pulse_r = 1.0 + 0.15 * math.sin(st * 3)
            drop_a2 = alpha_t(f, 22.0, 6.0)
            layer_d2 = Image.new("RGBA", (W, H), (0,0,0,0))
            dl2 = ImageDraw.Draw(layer_d2)
            draw_drop_icon(dl2, 165, H//2 - 180, int(38 * pulse_r * drop_a2), DEEP_ROSE)
            img = Image.alpha_composite(img.convert("RGBA"), layer_d2)
            d = ImageDraw.Draw(overlay)

        # Text
        line1_a = alpha_t(f, 21.3, 6.7)
        care_a  = alpha_t(f, 22.8, 5.2)

        if line1_a > 0.05:
            draw_text_centered(d, "That mother", W//2 - 50, H//2 - 260, font("sans", 44), NUDE_BROWN)
            draw_text_centered(d, "silently enduring…", W//2 - 50, H//2 - 200, font("sans", 40), NUDE_BROWN)
            draw_text_centered(d, "painful periods?", W//2 - 50, H//2 - 148, font("sans", 40), NUDE_BROWN)
            draw_text_centered(d, "You deserve…", W//2 - 50, H//2 - 80, font("serif", 48), DARK_BROWN)

        if care_a > 0.05:
            care_scale = ease_bounce(clamp((t - 22.8) / 0.6))
            fn_care = font("serif", int(76 * care_scale))
            if care_scale > 0.05:
                img = draw_glow_text(ImageDraw.Draw(img.convert("RGBA")), img.convert("RGBA"),
                                     "CARE.", W//2 - 50, H//2 + 20, fn_care, DEEP_ROSE, SOFT_PINK, 25)
                d = ImageDraw.Draw(overlay)
            # "too" in smaller text below
            if care_a > 0.4:
                ta = int(220 * ((care_a - 0.4)/0.6))
                draw_text_centered(d, "too.  🤍", W//2 - 50, H//2 + 110, font("serif", 52), NUDE_BROWN)

    # ── SCENE 6: CALL TO ACTION 28–38s ───────────────────────────────────────
    elif 28 <= t < 38:
        st = t - 28

        # Warm background wash
        wash = Image.new("RGBA", (W, H), (*DEEP_ROSE, int(25 * min(st, 3.0) / 3.0)))
        img = Image.alpha_composite(img.convert("RGBA"), wash)
        d = ImageDraw.Draw(overlay)

        # Crossed-out "whispering" graphic
        whisper_prog = ease_out(anim_t(f, 28.2, 0.8))
        if whisper_prog > 0.1:
            fn_w = font("serif", 50)
            wx = W//2
            wy = H//2 - 280
            bbox_w = fn_w.getbbox("STOP WHISPERING")
            tw_w = bbox_w[2] - bbox_w[0]
            draw_text_centered(d, "STOP WHISPERING", wx, wy, fn_w, NUDE_BROWN)
            # Draw strikethrough progressively
            st_prog = clamp((t - 28.6) / 0.5)
            if st_prog > 0:
                d.line([(wx - tw_w//2, wy + 2), (wx - tw_w//2 + int(tw_w * st_prog), wy + 2)],
                       fill=rgba(DEEP_ROSE, 240), width=5)

        # Speech bubble right side
        bubble_scale = ease_bounce(clamp((t - 29.0) / 0.7))
        bubble_a = alpha_t(f, 29.0, 9.0)
        if bubble_scale > 0.05 and bubble_a > 0.05:
            bbl = Image.new("RGBA", (W, H), (0,0,0,0))
            bd2 = ImageDraw.Draw(bbl)
            draw_speech_bubble(bd2, W - 220, H//2 - 100, 340, 180,
                               ["Talk to your", "daughters."],
                               font("round", 40), DARK_BROWN,
                               bubble_scale * bubble_a, "right")
            img = Image.alpha_composite(img.convert("RGBA"), bbl)
            d = ImageDraw.Draw(overlay)

        # Teach icon (book)
        book_prog = ease_out(anim_t(f, 30.5, 0.8))
        if book_prog > 0.05:
            bx, by = 150, H//2 + 20
            bs = int(70 * book_prog)
            d.rounded_rectangle([bx-bs, by-bs*0.7, bx+bs, by+bs*0.7],
                                 radius=8, fill=rgba(WARM_AMBER, int(200*book_prog)),
                                 outline=rgba(NUDE_BROWN, int(180*book_prog)), width=3)
            d.line([(bx, by-int(bs*0.7)), (bx, by+int(bs*0.7))],
                   fill=rgba(NUDE_BROWN, int(150*book_prog)), width=3)

        # "WITHOUT FEAR. WITHOUT SHAME." cascading
        fn_bold = font("serif", 54)
        wf_a = alpha_t(f, 31.5, 6.5)
        ws_a = alpha_t(f, 32.5, 5.5)
        if wf_a > 0.05:
            draw_text_centered(d, "WITHOUT FEAR.", W//2, H//2 + 80, fn_bold, DARK_BROWN)
        if ws_a > 0.05:
            draw_text_centered(d, "WITHOUT SHAME.", W//2, H//2 + 155, fn_bold, DEEP_ROSE)

        # Bottom: main script lines
        fn_script = font("sans", 42)
        sc_a = alpha_t(f, 33.5, 4.5)
        if sc_a > 0.05:
            draw_text_centered(d, "Teach them.", W//2, H//2 + 240, fn_script, NUDE_BROWN)

    # ── SCENE 7: DIGNITY 38–48s ───────────────────────────────────────────────
    elif 38 <= t < 48:
        st = t - 38

        # Lilac wash
        lilac_wash = Image.new("RGBA", (W, H), (*LILAC, int(30 * min(st, 2.0) / 2.0)))
        img = Image.alpha_composite(img.convert("RGBA"), lilac_wash)

        # LUXURY crossed out
        lux_prog = ease_out(anim_t(f, 38.2, 0.8))
        lux_a = alpha_t(f, 38.2, 9.8)
        if lux_prog > 0.1:
            fn_l = font("serif", 52)
            draw_text_centered(d, "Not LUXURY.", W//2, H//2 - 250, fn_l, NUDE_BROWN)
            # Strikethrough
            cross_prog = clamp((t - 38.7) / 0.5)
            if cross_prog > 0:
                bb_l = fn_l.getbbox("Not LUXURY.")
                lw = bb_l[2] - bb_l[0]
                d.line([(W//2 - lw//2, H//2 - 250), (W//2 - lw//2 + int(lw * cross_prog), H//2 - 250)],
                       fill=rgba(DEEP_ROSE, 230), width=5)

        # DIGNITY hero word
        dig_a = alpha_t(f, 39.2, 8.8)
        if dig_a > 0.05:
            dig_scale = ease_bounce(clamp((t - 39.2) / 0.7))
            fn_dig = font("serif", int(100 * dig_scale))
            if dig_scale > 0.05:
                img = draw_glow_text(None, img.convert("RGBA"),
                                     "DIGNITY", W//2, H//2 - 80, fn_dig, DEEP_ROSE, LILAC, 30)
                d = ImageDraw.Draw(overlay)
                # Crown emoji area
                crown_a = int(220 * dig_a * dig_scale)
                fn_crown = font("round", int(60 * dig_scale))
                draw_text_centered(d, "👑", W//2 + 250, H//2 - 130, fn_crown, WARM_AMBER)

        # Floating words layer
        float_layer = Image.new("RGBA", (W, H), (0,0,0,0))
        fld = ImageDraw.Draw(float_layer)
        word_list = [
            ("dignity", LILAC, 60, 0.25, 0.0),
            ("health", SOFT_PINK, 46, 0.75, 1.5),
            ("care", NUDE_BROWN, 38, 0.15, 0.8),
            ("confidence", LILAC, 40, 0.80, 2.5),
            ("support", SOFT_PINK, 36, 0.45, 3.2),
            ("strength", WARM_AMBER, 34, 0.60, 1.0),
        ]
        for word, col, sz, xf, delay in word_list:
            wt = st - delay
            if wt < 0:
                continue
            fn_fw = font("serif", sz)
            cycle = 6.0
            phase = (wt % cycle) / cycle
            wx_ = int(xf * W)
            wy_ = int(H * 0.92 - phase * H * 1.05)
            if -80 < wy_ < H + 60:
                wa = int(160 * math.sin(math.pi * phase))
                bb_fw = fn_fw.getbbox(word)
                fld.text((wx_ - (bb_fw[2]-bb_fw[0])//2, wy_), word, font=fn_fw, fill=rgba(col, wa))
        img = Image.alpha_composite(img.convert("RGBA"), float_layer)
        d = ImageDraw.Draw(overlay)

        # Menstrual health icons halo
        icon_a = alpha_t(f, 40.5, 7.5)
        if icon_a > 0.1:
            icons_prog = ease_out(anim_t(f, 40.5, 1.5))
            icon_cx, icon_cy = W//2, H//2 + 160
            icon_r = 220
            for i, (ic_fn, ic_color) in enumerate([
                (lambda d,x,y,s,p: draw_pad_icon(d,x,y,s,p,SOFT_PINK,NUDE_BROWN), SOFT_PINK),
                (lambda d,x,y,s,p: draw_calendar_icon(d,x,y,s,p,LILAC,NUDE_BROWN), LILAC),
                (lambda d,x,y,s,p: draw_drop_icon(d,x,y,int(s*p),DEEP_ROSE), DEEP_ROSE),
                (lambda d,x,y,s,p: draw_hibiscus(d,x,y,s,p,NUDE_BROWN), NUDE_BROWN),
            ]):
                angle = math.pi * 2 * i / 4 - math.pi/2
                ix = icon_cx + int(math.cos(angle) * icon_r)
                iy = icon_cy + int(math.sin(angle) * icon_r)
                glow_phase = 0.7 + 0.3 * math.sin(st * 2 + i * math.pi/2)
                icon_layer = Image.new("RGBA", (W, H), (0,0,0,0))
                ild = ImageDraw.Draw(icon_layer)
                ic_fn(ild, ix, iy, 55, icons_prog * glow_phase * icon_a)
                img = Image.alpha_composite(img.convert("RGBA"), icon_layer)
                d = ImageDraw.Draw(overlay)

        # Script text bottom
        fn_s = font("sans", 40)
        sc2_a = alpha_t(f, 41.0, 7.0)
        if sc2_a > 0.05:
            draw_text_centered(d, "Menstrual hygiene is", W//2, H//2 + 320, fn_s, NUDE_BROWN)
            draw_text_centered(d, "every girl's right.", W//2, H//2 + 375, fn_s, NUDE_BROWN)
        sc3_a = alpha_t(f, 43.0, 5.0)
        if sc3_a > 0.05:
            draw_text_centered(d, "Health without the complexity.", W//2, H//2 + 450, font("serif", 42), DEEP_ROSE)

    # ── SCENE 8: CTA SCREEN 48–60s ────────────────────────────────────────────
    elif t >= 48:
        st = t - 48

        # CTA background gradient
        cta_bg = Image.new("RGBA", (W, H), (0,0,0,0))
        bg_arr = np.array(cta_bg)
        for y in range(H):
            tt = y / H
            r = int(200*(1-tt) + 245*tt)
            g = int(180*(1-tt) + 237*tt)
            b = int(226*(1-tt) + 224*tt)
            bg_arr[y, :] = [r, g, b, int(240 * min(st/1.5, 1.0))]
        cta_bg = Image.fromarray(bg_arr.astype(np.uint8))
        img = Image.alpha_composite(img.convert("RGBA"), cta_bg)
        d = ImageDraw.Draw(overlay)

        # Logo (large, centered top)
        logo_a = ease_out(anim_t(f, 48.5, 1.0))
        logo_scale = 1.3 * logo_a
        if logo_a > 0.05:
            logo_pulse = 1.0 + 0.03 * math.sin(st * 2)
            glow_layer2 = Image.new("RGBA", (W, H), (0,0,0,0))
            gd4 = ImageDraw.Draw(glow_layer2)
            for r_g in range(120, 0, -10):
                a_g = int(40 * logo_a * (1 - r_g/120))
                gd4.ellipse([W//2 - r_g, 280 - r_g, W//2 + r_g, 280 + r_g], fill=rgba(LILAC, a_g))
            img = Image.alpha_composite(img.convert("RGBA"), glow_layer2)
            d = ImageDraw.Draw(overlay)
            draw_logo(d, W//2, 300, scale=logo_scale * logo_pulse, alpha=int(240 * logo_a))

        # "HAPPY WORLD MENSTRUAL HYGIENE DAY"
        title_a = ease_out(anim_t(f, 49.5, 1.2))
        if title_a > 0.05:
            fn_t1 = font("round", 38)
            fn_t2 = font("serif", 62)
            fn_t3 = font("round", 38)
            draw_text_centered(d, "🌸 HAPPY", W//2, 520, fn_t1, DEEP_ROSE)
            draw_text_centered(d, "WORLD MENSTRUAL", W//2, 590, fn_t2, NUDE_BROWN)
            draw_text_centered(d, "HYGIENE DAY 🌸", W//2, 660, fn_t2, NUDE_BROWN)

        # "May 28" date badge
        date_a = ease_out(anim_t(f, 50.2, 0.8))
        if date_a > 0.05:
            d.rounded_rectangle([W//2 - 100, 700, W//2 + 100, 760],
                                 radius=30, fill=rgba(DEEP_ROSE, int(220*date_a)))
            draw_text_centered(d, "May 28", W//2, 730, font("sans", 36), CREAM)

        # "Follow for more" card
        follow_a = ease_out(anim_t(f, 51.0, 1.0))
        if follow_a > 0.05:
            d.rounded_rectangle([W//2 - 280, 830, W//2 + 280, 1010],
                                 radius=24, fill=rgba(CREAM, int(240*follow_a)),
                                 outline=rgba(SOFT_PINK, int(220*follow_a)), width=4)
            # Shimmer sweep
            shimmer_x = int((-280 + (st % 3) / 3 * 760) - 280)
            if 0 < shimmer_x + 280 < 560:
                shimmer_layer = Image.new("RGBA", (W, H), (0,0,0,0))
                sd = ImageDraw.Draw(shimmer_layer)
                sx = W//2 - 280 + shimmer_x + 280
                sd.rectangle([sx - 30, 830, sx + 30, 1010], fill=rgba(WHITE, 60))
                img = Image.alpha_composite(img.convert("RGBA"), shimmer_layer)
                d = ImageDraw.Draw(overlay)
            fn_f1 = font("round", 36)
            fn_f2 = font("round", 32)
            draw_text_centered(d, "Follow for more", W//2, 880, fn_f1, DARK_BROWN)
            draw_text_centered(d, "health without the", W//2, 930, fn_f2, NUDE_BROWN)
            draw_text_centered(d, "complexity", W//2, 976, fn_f2, NUDE_BROWN)

        # Social handle
        handle_a = ease_out(anim_t(f, 52.0, 0.8))
        if handle_a > 0.05:
            fn_h = font("sans", 42)
            chars = "@DrPsCorner"
            visible_chars = max(1, int(len(chars) * min((st - 4.0) / 1.5, 1.0)))
            handle_text = chars[:visible_chars]
            draw_text_centered(d, "📱 " + handle_text, W//2, 1070, fn_h, DEEP_ROSE)
            # Cursor blink
            if visible_chars < len(chars) or int(st * 2) % 2 == 0:
                bbox_h = fn_h.getbbox("📱 " + handle_text)
                cx_h = W//2 + (bbox_h[2]-bbox_h[0])//2 + 3
                d.rectangle([cx_h, 1052, cx_h + 3, 1090], fill=rgba(DEEP_ROSE, 220))

        # Petal rain
        petal_layer = Image.new("RGBA", (W, H), (0,0,0,0))
        pd = ImageDraw.Draw(petal_layer)
        rng_p = np.random.default_rng(int(st * 20))
        for _ in range(20):
            px = int(rng_p.uniform(0, W))
            py = int((rng_p.uniform(0, 1.0) * H + st * 120) % (H + 40)) - 20
            pr = int(rng_p.uniform(8, 22))
            pc = rng_p.choice([SOFT_PINK, LILAC])
            pangle = rng_p.uniform(0, 360)
            petal_pts = []
            for j in range(8):
                a = math.radians(pangle + j * 45)
                ex = px + int(math.cos(a) * pr)
                ey = py + int(math.sin(a) * pr * 0.5)
                petal_pts.append((ex, ey))
            if len(petal_pts) >= 3:
                pd.polygon(petal_pts, fill=rgba(tuple(pc), 120))
        img = Image.alpha_composite(img.convert("RGBA"), petal_layer)
        d = ImageDraw.Draw(overlay)

        # Brand lockup bottom
        brand_a = ease_out(anim_t(f, 53.0, 1.0))
        if brand_a > 0.05:
            # Line
            d.line([(W//4, 1140), (3*W//4, 1140)], fill=rgba(NUDE_BROWN, int(120*brand_a)), width=2)
            draw_text_centered(d, "🌺 DR. P'S CORNER 🌺", W//2, 1190, font("round", 40), NUDE_BROWN)
            draw_hibiscus(d, W//2 - 320, 1190, 28, brand_a, SOFT_PINK)
            draw_hibiscus(d, W//2 + 320, 1190, 28, brand_a, LILAC)

        # Tagline
        tag_a = ease_out(anim_t(f, 54.5, 1.0))
        if tag_a > 0.05:
            draw_text_centered(d, "Health. Dignity. Care.", W//2, 1270, font("serif", 46), DEEP_ROSE)

    # ── FINALIZE FRAME ────────────────────────────────────────────────────────
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    return img.convert("RGB")

# ─── VIDEO WRITER ─────────────────────────────────────────────────────────────
def main():
    import imageio
    import os
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()

    print(f"Generating {TOTAL_FRAMES} frames at {W}x{H} @ {FPS}fps...")
    print(f"Output: {OUTPUT_VIDEO}")

    writer = imageio.get_writer(
        OUTPUT_VIDEO,
        fps=FPS,
        codec="libx264",
        quality=8,
        ffmpeg_params=[
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-crf", "20",
            "-movflags", "+faststart",
        ],
        macro_block_size=1,
    )

    for f in range(TOTAL_FRAMES):
        if f % (FPS * 5) == 0:
            secs = f // FPS
            print(f"  [{f}/{TOTAL_FRAMES}] {secs}s / {DURATION}s", flush=True)
        frame = build_frame(f)
        writer.append_data(np.array(frame))

    writer.close()
    size_mb = os.path.getsize(OUTPUT_VIDEO) / 1024 / 1024
    print(f"\nDone! {OUTPUT_VIDEO} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()
