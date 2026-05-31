"""
Dr. P's Corner — Cinematic Medical Trailer Generator
=====================================================
Transforms the avatar talking video into a Netflix-style medical
documentary trailer using WaveSpeed Nano Banana 2 Edit (T2I) + Wan 2.1 (I2V).

Pipeline:
  1. Generate cinematic stills for each scene  (WaveSpeed Nano Banana 2 Edit)
  2. Animate each still into a video clip      (WaveSpeed Wan 2.1 I2V)
  3. Process avatar video → 9:16 portrait
  4. Assemble scenes with transitions + PiP
  5. Apply motion-graphics text overlays
  6. Apply cinematic colour grading + vignette
  7. Extract avatar audio and merge into final output
  8. Export 1080×1920 @ 24fps

Usage:
    python cinematic_trailer.py \
        --avatar /path/to/VID20260531WA0016.mp4 \
        --output drp_trailer.mp4

Environment:
    WAVESPEED_API_KEY=wsk_live_...
"""

import argparse
import base64
import io as _io
import math
import os
import shutil
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

# ─── CONFIG ───────────────────────────────────────────────────────────────────
W, H   = 1080, 1920
FPS    = 24
WAVESPEED_BASE = "https://api.wavespeed.ai/api/v3"

# T2I: Nano Banana 2 Edit (hyper-realistic image editing / generation)
T2I_MODEL       = "google/nano-banana-2/edit"
T2I_FALLBACK    = "wavespeed-ai/flux-dev"       # fallback if NB2 fails

# I2V: Wan 2.1 480p (animate stills into cinematic clips)
I2V_MODEL       = "wavespeed-ai/wan-2.1/i2v-480p"

AVATAR_PATH = "/root/.claude/uploads/b13fbee6-c7ab-4c76-ac28-394ef5e2fdca/c0f660bc-VID20260531WA0016.mp4"

# Load .env
_env = Path(__file__).parent / ".env"
if _env.exists():
    for _l in _env.read_text().splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _, _v = _l.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# ─── BRAND PALETTE ────────────────────────────────────────────────────────────
BEIGE      = (245, 237, 224)
SOFT_PINK  = (242, 184, 198)
LILAC      = (200, 180, 226)
NUDE_BROWN = (160, 120,  90)
CREAM      = (255, 248, 242)
DEEP_ROSE  = (212,  96, 122)
DARK       = ( 10,   6,   4)
MID_DARK   = ( 28,  18,  12)
BLOOD_RED  = (160,  20,  15)
AMBER      = (200, 120,  40)

# ─── SCENE DEFINITIONS — synced to Whisper timestamps ─────────────────────────
# Whisper segments:
#  [ 0.00 –  3.12]  "Now, I know you guys are itching to hear what these habits are."
#  [ 3.72 –  8.50]  "One of the biggest contributors is...unhealthy fats, sitting"
#  [ 8.50 – 12.62]  "for long periods and barely moving affects healthy blood circulation."
#  [13.24 – 16.78]  "Uncontrolled diabetes can quietly damage the arteries over time."
#  [17.36 – 20.44]  "High blood pressure puts repeated stress on blood vessel walls."
#  [21.00 – 27.42]  "chronic stress...A lot of people unfortunately fall under this category."
#  [27.42 – 30.10]  "And the chief, the boss at the top smoking."
#  [30.38 – 32.38]  "Smoking directly damages blood vessel."
#
# avatar_mode: "full" | "pip" | "cut"
SCENES = [
    # 0–3.12s: avatar speaks intro line — full frame
    {
        "id":          "intro",
        "start":        0.0,  "end":  3.2,
        "avatar_mode": "full",
        "text":        None,
        "t2i_prompt":  None,
        "i2v_prompt":  None,
    },
    # 3.12–3.72s: brief dramatic bloodstream cut (between lines)
    {
        "id":          "bloodstream",
        "start":        3.1,  "end":  4.0,
        "avatar_mode": "cut",
        "text":        None,
        "t2i_prompt": (
            "Extreme macro cinematic interior of a human blood vessel tunnel, "
            "dark deep-red glistening walls, thousands of red blood cells drifting "
            "in viscous fluid, bioluminescent particles floating, volumetric god rays "
            "penetrating darkness, amber and deep crimson tones, "
            "9:16 vertical portrait photorealistic 8K shallow depth of field film grain cinematic"
        ),
        "i2v_prompt": (
            "Slow cinematic push through blood vessel tunnel, particles drifting, "
            "subtle pulse and flow, god rays shifting, atmospheric depth, slow motion"
        ),
    },
    # 3.72–8.50s: "one of the biggest contributors...unhealthy fats" — pip on food imagery
    {
        "id":          "unhealthy_fat",
        "start":        3.72, "end":  8.5,
        "avatar_mode": "pip",
        "text":        None,
        "t2i_prompt": (
            "Hyper-realistic cinematic macro close-up of greasy fast food floating "
            "in deep darkness — glistening burger, oily fries, sugary drink with condensation, "
            "fat droplets catching dramatic side-lighting, microscopic fat particles "
            "visible in foreground, dark premium moody medical aesthetic, "
            "9:16 vertical portrait photorealistic 8K deep shadows cinematic lens"
        ),
        "i2v_prompt": (
            "Slow cinematic reveal of fast food in darkness, fat particles drifting forward, "
            "dramatic side-lighting shifts, macro details emerging, heavy and moody"
        ),
    },
    # 8.0–8.6s: brief plaque flash — visual consequence of fat as "sitting" begins
    {
        "id":          "plaque_buildup",
        "start":        8.0,  "end":  8.7,
        "avatar_mode": "cut",
        "text":        None,
        "t2i_prompt": (
            "Cinematic medical cross-section of human artery interior: "
            "yellowish cholesterol plaque clinging to deep-red vessel walls, "
            "blood flow visibly narrowed, sticky fat deposits layering on artery surface, "
            "dark atmospheric medical documentary aesthetic, amber and dark crimson palette, "
            "9:16 vertical portrait photorealistic 8K volumetric depth"
        ),
        "i2v_prompt": (
            "Slow push through narrowing artery, plaque slowly building on walls, "
            "blood flow becoming sluggish, cinematic medical atmosphere, dark and tense"
        ),
    },
    # 8.50–12.62s: "sitting for long periods and barely moving" — sedentary silhouette
    {
        "id":          "sedentary",
        "start":        8.5,  "end": 12.7,
        "avatar_mode": "pip",
        "text":        None,
        "t2i_prompt": (
            "Cinematic dark portrait silhouette: person sitting motionless alone "
            "in a dim room, hunched posture, single harsh rim light from the side, "
            "deep oppressive shadows consuming 80% of frame, heavy atmospheric haze, "
            "film noir medical aesthetic, "
            "9:16 vertical portrait photorealistic 8K grain shallow depth of field"
        ),
        "i2v_prompt": (
            "Slow cinematic camera circle around sedentary silhouette, light slowly "
            "dimming, atmospheric haze thickening, emotional stillness, very slow"
        ),
    },
    # 12.62–13.24s: brief avatar beat between lines — cut back to avatar full
    {
        "id":          "avatar_beat_1",
        "start":       12.7,  "end": 13.3,
        "avatar_mode": "full",
        "text":        None,
        "t2i_prompt":  None,
        "i2v_prompt":  None,
    },
    # 13.24–16.78s: "uncontrolled diabetes can quietly damage" — diabetes visual
    {
        "id":          "diabetes",
        "start":       13.2,  "end": 16.9,
        "avatar_mode": "cut",
        "text":        None,
        "t2i_prompt": (
            "Extreme macro cinematic inside a human blood vessel: sharp crystalline "
            "glucose particles flowing aggressively through dark blood, artery lining "
            "showing inflammation — subtle orange-red inflammatory glow on vessel walls, "
            "micro-tears beginning, medical biopunk aesthetic, dark crimson and amber "
            "tones with fiery inflammatory highlights, "
            "9:16 vertical portrait photorealistic 8K cinematic"
        ),
        "i2v_prompt": (
            "Glucose crystals flowing through blood vessel, inflammatory glow pulsing "
            "on artery walls, slow cinematic push through damaged vessel interior, intense"
        ),
    },
    # 17.36–20.44s: "high blood pressure puts repeated stress" — pressure visual
    {
        "id":          "blood_pressure",
        "start":       17.3,  "end": 20.5,
        "avatar_mode": "pip",
        "text":        None,
        "t2i_prompt": (
            "Cinematic macro human artery under extreme hypertensive pressure: "
            "vessel walls bulging dramatically, blood surging violently with visible "
            "pressure waves slamming vessel walls, white pressure flares at impact points, "
            "deep dark red with stark white highlights, walls visibly straining, "
            "slow-motion freeze-frame energy, "
            "9:16 vertical portrait photorealistic 8K cinematic impact dramatic contrast"
        ),
        "i2v_prompt": (
            "Blood pressure waves slamming artery walls in slow motion, vessel bulging "
            "and recoiling rhythmically, dramatic cinematic impact, deep heartbeat pulse"
        ),
    },
    # 20.44–21.0s: brief avatar beat before stress section
    {
        "id":          "avatar_beat_2",
        "start":       20.5,  "end": 21.1,
        "avatar_mode": "full",
        "text":        None,
        "t2i_prompt":  None,
        "i2v_prompt":  None,
    },
    # 21.0–27.42s: "chronic stress...a lot of people fall under this category"
    {
        "id":          "stress",
        "start":       21.0,  "end": 27.5,
        "avatar_mode": "cut",
        "text":        None,
        "t2i_prompt": (
            "Cinematic dark atmospheric portrait: emotionally drained silhouette, "
            "face faintly illuminated by cold phone screen glow in very dark room, "
            "dark smoke wisps rising and curling around the figure, irregular glowing "
            "particles representing cortisol drifting through air, heavy oppressive mood, "
            "emotional weight, "
            "9:16 vertical portrait photorealistic 8K grain cinematic shallow focus"
        ),
        "i2v_prompt": (
            "Dark smoke slowly expanding around stressed silhouette, particles drifting, "
            "phone light flickering slightly, atmosphere becoming heavier and more oppressive"
        ),
    },
    # 27.42–30.10s: "and the chief, the boss at the top...smoking" — dramatic reveal
    {
        "id":          "smoking_reveal",
        "start":       27.4,  "end": 30.2,
        "avatar_mode": "pip",
        "text":        None,
        "t2i_prompt": (
            "DRAMATIC cinematic reveal: dark silhouette smoking in near-total darkness, "
            "cigarette ember burning intensely bright, thick white-grey smoke billowing "
            "to fill entire frame, smoke tendrils at edges morphing into microscopic "
            "damaged blood vessel structures — darkened, narrowed, necrotic, "
            "deep charcoal and near-black tones, ember as only light source, "
            "9:16 vertical portrait photorealistic 8K extreme atmosphere film grain"
        ),
        "i2v_prompt": (
            "Slow dramatic reveal: smoke expanding to fill frame, ember glowing intensely, "
            "smoke morphing into damaged blood vessels, cinematic impact, very slow motion"
        ),
    },
    # 30.38–32.38s: "smoking directly damages blood vessel" — artery damage extreme close
    {
        "id":          "artery_damage",
        "start":       30.3,  "end": 32.5,
        "avatar_mode": "cut",
        "text":        None,
        "t2i_prompt": (
            "Extreme macro cinematic artery interior: healthy left half "
            "(bright red, open, clean walls) vs severely diseased right half "
            "(dark, narrowed, thick black-brown plaque coating walls, "
            "tiny white blood clot forming at narrowest point), blood flow nearly blocked, "
            "dramatic split contrast, dark medical documentary aesthetic, "
            "9:16 vertical portrait photorealistic 8K cinematic"
        ),
        "i2v_prompt": (
            "Healthy artery transforming to blocked vessel, plaque accelerating, "
            "blood flow stopping, tiny clot forming in slow cinematic motion, intense"
        ),
    },
    # 32.38s+: avatar returns full frame, brand card fades in
    {
        "id":          "outro",
        "start":       32.3,  "end": 37.0,
        "avatar_mode": "full",
        "text":        None,
        "t2i_prompt":  None,
        "i2v_prompt":  None,
    },
]

# ─── FONT HELPERS ─────────────────────────────────────────────────────────────
FONT_PATHS = {
    "serif": [
        "/root/.fonts/PlayfairDisplay-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    ],
    "sans": [
        "/root/.fonts/DMSans-Medium.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ],
}
_font_cache: dict = {}

def font(kind: str, size: int) -> ImageFont.ImageFont:
    size = max(1, size)
    key = (kind, size)
    if key in _font_cache:
        return _font_cache[key]
    for p in FONT_PATHS.get(kind, []):
        if os.path.exists(p):
            _font_cache[key] = ImageFont.truetype(p, size)
            return _font_cache[key]
    _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]

# ─── EASING ───────────────────────────────────────────────────────────────────
def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

def ease_out(t):
    return 1 - (1 - clamp(t)) ** 3

def ease_in_out(t):
    t = clamp(t)
    return 3*t**2 - 2*t**3

# ─── CINEMATIC COLOUR GRADE ───────────────────────────────────────────────────
def apply_cinematic_grade(img: Image.Image, strength: float = 1.0) -> Image.Image:
    """Dark cinematic grade: shadow crush, warm tint, desaturate, film grain."""
    arr = np.array(img).astype(np.float32)

    # Underexpose slightly
    arr *= 0.86

    # Contrast S-curve
    a = arr / 255.0
    a = 0.5 * np.sin(np.pi * (a - 0.5)) + 0.5
    arr = a * 255.0

    # Warm shadow tint
    luma = arr.mean(axis=2)
    sh = np.clip(1.0 - luma / 100.0, 0, 1)[:, :, np.newaxis]
    arr[:, :, 0:1] += sh * 14 * strength
    arr[:, :, 1:2] += sh * 4  * strength
    arr[:, :, 2:3] -= sh * 10 * strength

    # Cool lilac highlight tint
    hi = np.clip((luma - 185.0) / 70.0, 0, 1)[:, :, np.newaxis]
    arr[:, :, 0:1] += hi * 6  * strength
    arr[:, :, 1:2] += hi * 2  * strength
    arr[:, :, 2:3] += hi * 12 * strength

    # Crush blacks
    arr = np.maximum(arr - 10, 0)
    arr = np.clip(arr, 0, 255).astype(np.uint8)

    graded = Image.fromarray(arr)
    graded = ImageEnhance.Color(graded).enhance(0.80)

    # Film grain
    noise = np.random.randint(-12, 13, np.array(graded).shape, dtype=np.int16)
    grain_arr = np.clip(np.array(graded).astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(grain_arr)

def apply_vignette(img: Image.Image, strength: float = 0.6) -> Image.Image:
    """Strong cinematic vignette."""
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(vig)
    for i in range(60):
        r = W // 2 + i * 12
        alpha = int(strength * 255 * (i / 60) ** 2)
        d.ellipse([W//2 - r, H//2 - r*2, W//2 + r, H//2 + r*2],
                  outline=(0, 0, 0, min(alpha, 255)), width=18)
    vig = vig.filter(ImageFilter.GaussianBlur(30))
    return Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")

# ─── AVATAR → PORTRAIT ────────────────────────────────────────────────────────
def avatar_to_portrait(frame: Image.Image, mode: str,
                        cin_frame: Image.Image = None) -> Image.Image:
    """Convert 640×360 avatar frame to 1080×1920 portrait."""
    iw, ih = frame.size

    if mode == "full":
        # Scale avatar to full width
        aw, ah = W, int(ih * W / iw)
        av = frame.resize((aw, ah), Image.LANCZOS)

        # Blurred + darkened full-frame bg
        bh_scale = H / ih
        bw = int(iw * bh_scale)
        bg = frame.resize((bw, H), Image.LANCZOS)
        if bw > W:
            bg = bg.crop(((bw - W) // 2, 0, (bw - W) // 2 + W, H))
        else:
            pad = Image.new("RGB", (W, H), DARK)
            pad.paste(bg, ((W - bw) // 2, 0))
            bg = pad
        bg = bg.filter(ImageFilter.GaussianBlur(28))
        bg = Image.blend(bg, Image.new("RGB", (W, H), DARK), 0.55)

        # Shallow depth blur on avatar edges
        av_blur = av.filter(ImageFilter.GaussianBlur(4))
        mask = Image.new("L", (aw, ah), 0)
        md = ImageDraw.Draw(mask)
        md.rectangle([60, 0, aw-60, ah], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(40))
        av_sharp = Image.composite(av, av_blur, mask)

        ay = (H - ah) // 2
        bg.paste(av_sharp, (0, ay))
        return bg

    elif mode == "pip":
        # Full-frame cinematic bg
        base = cin_frame.resize((W, H), Image.LANCZOS) if cin_frame else Image.new("RGB", (W, H), DARK)

        # Avatar in lower-right corner at 36% width
        pip_w = int(W * 0.36)
        pip_h = int(pip_w * ih / iw)
        pip = frame.resize((pip_w, pip_h), Image.LANCZOS)
        pip = pip.filter(ImageFilter.GaussianBlur(1))  # subtle softening

        border = 6
        pip_b = Image.new("RGB", (pip_w + border*2, pip_h + border*2), (18, 10, 6))
        pip_b.paste(pip, (border, border))

        px = W - pip_w - border*2 - 36
        py = H - pip_h - border*2 - 110

        # Shadow
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rectangle(
            [px-18, py-18, px+pip_w+border*2+18, py+pip_h+border*2+18],
            fill=(0, 0, 0, 90)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(14))
        base = Image.alpha_composite(base.convert("RGBA"), shadow).convert("RGB")
        base.paste(pip_b, (px, py))
        return base

    # "cut" — cinematic only
    return cin_frame.resize((W, H), Image.LANCZOS) if cin_frame else Image.new("RGB", (W, H), DARK)

# ─── MOTION GRAPHICS ──────────────────────────────────────────────────────────
def draw_text_overlay(img: Image.Image, text: str, progress: float) -> Image.Image:
    """Minimal cinematic text fade-in from bottom."""
    if not text or progress <= 0:
        return img
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lines = text.strip().split("\n")
    fnt = font("sans", 52)
    line_h = 68
    total_h = len(lines) * line_h
    base_y = H - 240

    alpha = int(240 * ease_out(progress))
    slide = int((1 - ease_out(progress)) * 28)

    for i, line in enumerate(lines):
        bb = fnt.getbbox(line)
        x = (W - (bb[2] - bb[0])) // 2
        y = base_y - total_h + i * line_h + slide
        d.text((x + 2, y + 2), line, font=fnt, fill=(0, 0, 0, int(alpha * 0.5)))
        d.text((x, y), line, font=fnt, fill=(*CREAM, alpha))

    if progress > 0.5:
        la = int(160 * ease_out((progress - 0.5) * 2))
        sep_y = base_y - total_h - 18 + slide
        d.line([(W//2 - 70, sep_y), (W//2 + 70, sep_y)], fill=(*SOFT_PINK, la), width=2)

    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")

def draw_heartbeat_line(img: Image.Image, t: float, alpha: int = 110) -> Image.Image:
    """Subtle ECG heartbeat line at bottom of frame."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y_base = H - 52
    pts = []
    for x in range(0, W, 3):
        phase = (x / W + t * 0.4) % 1.0
        if 0.44 < phase < 0.56:
            amp = int(70 * math.sin((phase - 0.44) / 0.12 * math.pi))
        else:
            amp = int(3 * math.sin((x / W + t * 0.5) * math.pi * 6))
        pts.append((x, y_base - amp))
    for i in range(len(pts) - 1):
        d.line([pts[i], pts[i+1]], fill=(*DEEP_ROSE, alpha), width=2)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")

def draw_brand_outro(img: Image.Image, progress: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = int(200 * ease_out(progress))
    d.rectangle([0, 0, W, H], fill=(6, 4, 2, a))
    if progress > 0.25:
        fa = int(255 * ease_out((progress - 0.25) / 0.75))
        fn1 = font("serif", 76)
        fn2 = font("sans", 40)
        t1 = "Dr. P's Corner"
        t2 = "Health Without The Complexity"
        bb1 = fn1.getbbox(t1)
        bb2 = fn2.getbbox(t2)
        d.text(((W - (bb1[2]-bb1[0])) // 2, H//2 - 65), t1, font=fn1, fill=(*CREAM, fa))
        d.text(((W - (bb2[2]-bb2[0])) // 2, H//2 + 44), t2, font=fn2, fill=(*SOFT_PINK, fa))
        d.line([(W//2 - 150, H//2 + 24), (W//2 + 150, H//2 + 24)],
               fill=(*NUDE_BROWN, int(fa * 0.55)), width=2)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")

def crossfade(a: Image.Image, b: Image.Image, t: float) -> Image.Image:
    t = clamp(t)
    if t <= 0: return a.convert("RGB")
    if t >= 1: return b.convert("RGB")
    return Image.blend(a.convert("RGB"), b.convert("RGB"), t)

# ─── WAVESPEED REST API ───────────────────────────────────────────────────────
def ws_headers(key: str) -> dict:
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

def img_to_b64(img: Image.Image) -> str:
    buf = _io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def _submit(key: str, model: str, payload: dict, max_retries: int = 8) -> str:
    """Submit a task; returns task_id. Retries on 429."""
    for attempt in range(max_retries):
        r = requests.post(
            f"{WAVESPEED_BASE}/{model}",
            headers=ws_headers(key), json=payload, timeout=60,
        )
        if r.status_code == 429:
            wait = min(30 * (2 ** attempt), 240)
            print(f"    429 rate limit — waiting {wait}s (attempt {attempt+1}/{max_retries})", flush=True)
            time.sleep(wait)
            continue
        if not r.ok:
            try:
                msg = r.json().get("message", r.text[:200])
            except Exception:
                msg = r.text[:200]
            raise RuntimeError(f"HTTP {r.status_code} from {model}: {msg}")
        return r.json()["data"]["id"]
    raise RuntimeError(f"Max retries exceeded for {model}")

def _poll(key: str, task_id: str, timeout: int = 900) -> str:
    """Poll until completed; returns output URL."""
    deadline = time.time() + timeout
    interval = 5
    while time.time() < deadline:
        r = requests.get(
            f"{WAVESPEED_BASE}/predictions/{task_id}/result",
            headers=ws_headers(key), timeout=30,
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
            raise RuntimeError(f"Task {status}: {data.get('error', 'unknown')}")
        print(f"    [{task_id[:10]}] {status}", flush=True)
        time.sleep(interval)
        interval = min(interval * 1.15, 15)
    raise TimeoutError(f"Task {task_id} timed out after {timeout}s")

def _download(url: str, suffix: str = ".mp4") -> Path:
    tmp = Path(tempfile.mktemp(suffix=suffix))
    urllib.request.urlretrieve(url, tmp)
    return tmp

# ─── SCENE GENERATION ─────────────────────────────────────────────────────────
def _make_dark_base(scene_id: str) -> Image.Image:
    """Dark noisy base image for Nano Banana inpainting."""
    colors = {
        "bloodstream":    (55,  8,  8),
        "unhealthy_fat":  (18, 12,  6),
        "plaque_buildup": (45, 14,  6),
        "sedentary":      ( 8,  8, 12),
        "diabetes":       (55, 12,  5),
        "blood_pressure": (65,  9,  7),
        "stress":         ( 8,  8, 15),
        "smoking_reveal": ( 6,  6,  6),
        "artery_damage":  (40, 10,  4),
    }
    color = colors.get(scene_id, (10, 8, 6))
    arr = np.full((1024, 576, 3), color, dtype=np.int16)
    arr = np.clip(arr + np.random.randint(-14, 15, arr.shape, dtype=np.int16), 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def _make_atmospheric_still(scene_id: str) -> Image.Image:
    """
    Create a cinematic atmospheric still using PIL when API credits are gone.
    Uses radial gradients, glow effects, and structural shapes per scene.
    """
    img = Image.new("RGB", (W, H), (4, 2, 2))
    arr = np.zeros((H, W, 3), dtype=np.float32)

    cx, cy = W // 2, H // 2
    ys = np.arange(H)[:, np.newaxis]
    xs = np.arange(W)[np.newaxis, :]
    dist = np.sqrt((xs - cx)**2 + (ys - cy)**2).astype(np.float32)
    max_d = np.sqrt(cx**2 + cy**2)

    if scene_id == "smoking_reveal":
        # Near-black with bright ember glow and drifting smoke wisps
        # Base: very dark charcoal
        arr[:] = [6, 5, 4]
        # Ember — intense orange-white hotspot at center-low
        ex, ey = cx, int(H * 0.72)
        ed = np.sqrt((xs - ex)**2 + (ys - ey)**2).astype(np.float32)
        ember = np.exp(-ed**2 / (80**2))
        arr[:, :, 0] += ember * 220
        arr[:, :, 1] += ember * 100
        arr[:, :, 2] += ember * 20
        # Smoke column — grey vertical gradient above ember
        smoke_x = np.abs(xs - ex).astype(np.float32)
        above = np.where(ys < ey, 1.0, 0.0)
        smoke = np.exp(-smoke_x**2 / (120**2)) * above
        height_fade = np.clip((ey - ys) / (ey * 0.9), 0, 1)
        arr[:, :, 0] += smoke * height_fade * 55
        arr[:, :, 1] += smoke * height_fade * 50
        arr[:, :, 2] += smoke * height_fade * 52

    elif scene_id == "artery_damage":
        # Cylindrical tunnel, healthy left / damaged right split
        # Background: deep crimson
        arr[:] = [25, 4, 2]
        # Tunnel walls — radial dark ring
        tunnel_r = int(W * 0.36)
        ring = np.clip((dist - tunnel_r) / 80, 0, 1)
        arr[:, :, 0] -= ring * 20
        arr[:, :, 1] -= ring * 3
        arr[:, :, 2] -= ring * 2
        # Left half: healthy — bright red open channel
        left_mask = (xs < cx).astype(np.float32)
        inner_l = np.clip(1.0 - dist / (tunnel_r * 0.7), 0, 1)
        arr[:, :, 0] += inner_l * left_mask * 160
        arr[:, :, 1] += inner_l * left_mask * 18
        arr[:, :, 2] += inner_l * left_mask * 12
        # Right half: diseased — dark amber-brown plaque buildup
        right_mask = (xs >= cx).astype(np.float32)
        plaque_r = tunnel_r * 0.30
        inner_r = np.clip(1.0 - dist / plaque_r, 0, 1)
        arr[:, :, 0] += inner_r * right_mask * 60
        arr[:, :, 1] += inner_r * right_mask * 25
        arr[:, :, 2] += inner_r * right_mask * 5
        # Plaque coating on right wall
        plaque_ring = np.clip(1.0 - np.abs(dist - tunnel_r * 0.55) / 40, 0, 1) * right_mask
        arr[:, :, 0] += plaque_ring * 80
        arr[:, :, 1] += plaque_ring * 35
        arr[:, :, 2] += plaque_ring * 5

    else:
        # Generic dark atmospheric: radial glow + noise
        colors = {
            "bloodstream":    ([60, 8, 6],   [180, 20, 10]),
            "unhealthy_fat":  ([14, 10, 5],  [50,  30, 10]),
            "plaque_buildup": ([40, 12, 5],  [120, 50, 15]),
            "sedentary":      ([5,  5, 10],  [20,  18, 40]),
            "diabetes":       ([55, 10, 4],  [200, 60, 10]),
            "blood_pressure": ([60, 8,  6],  [220, 30, 15]),
            "stress":         ([5,  5, 12],  [25,  15, 55]),
        }
        bg, glow = colors.get(scene_id, ([8, 6, 4], [60, 30, 15]))
        arr[:] = bg
        radial = np.exp(-dist**2 / (cx * 0.7)**2)
        for c in range(3):
            arr[:, :, c] += radial * glow[c]

    # Noise for film grain feel
    arr += np.random.uniform(-8, 8, arr.shape)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr).filter(ImageFilter.GaussianBlur(1))

def generate_still(key: str, scene: dict, cache_dir: Path, t2i_model: str = T2I_MODEL) -> Image.Image:
    """Generate a cinematic still; API first, local atmospheric fallback."""
    sid = scene["id"]
    still_path = cache_dir / f"{sid}_still.png"

    if still_path.exists():
        print(f"  [{sid}] Loading cached still", flush=True)
        return Image.open(still_path).convert("RGB")

    print(f"  [{sid}] Generating still with {t2i_model}…", flush=True)

    base_img = _make_dark_base(sid)
    b64_base = img_to_b64(base_img)
    payload = {
        "images":               [b64_base],
        "prompt":               scene["t2i_prompt"],
        "resolution":           "1k",
        "output_format":        "png",
        "enable_base64_output": False,
        "enable_image_search":  False,
        "enable_sync_mode":     False,
        "enable_web_search":    False,
    }

    url = None
    try:
        task_id = _submit(key, t2i_model, payload)
        print(f"    Task ID: {task_id}", flush=True)
        url = _poll(key, task_id, timeout=600)
    except Exception as e:
        print(f"    NB2 Edit failed ({e}), trying {T2I_FALLBACK}…", flush=True)
        try:
            payload_fb = {
                "prompt": scene["t2i_prompt"],
                "num_inference_steps": 28,
                "guidance_scale": 7.5,
                "size": "576*1024",
            }
            task_id = _submit(key, T2I_FALLBACK, payload_fb)
            print(f"    Fallback task ID: {task_id}", flush=True)
            url = _poll(key, task_id, timeout=600)
        except Exception as e2:
            print(f"    Both APIs failed ({e2}) — using local atmospheric still", flush=True)

    if url:
        tmp = _download(url, ".png")
        still = Image.open(tmp).convert("RGB")
        tmp.unlink(missing_ok=True)
    else:
        still = _make_atmospheric_still(sid)

    still = still.resize((W, H), Image.LANCZOS)
    still.save(still_path)
    print(f"    Still saved → {still_path}", flush=True)
    return still

def ken_burns(still: Image.Image, n_frames: int, scene_id: str) -> list:
    """
    Cinematic Ken Burns zoom/pan on a still image.
    Each scene gets a unique movement to avoid repetition.
    """
    iw, ih = still.size
    # Extra canvas so we can zoom in without black borders (20% overshoot)
    margin = 0.20
    bw = int(iw * (1 + margin))
    bh = int(ih * (1 + margin))
    padded = Image.new("RGB", (bw, bh), (0, 0, 0))
    padded.paste(still, ((bw - iw) // 2, (bh - ih) // 2))

    # Movement profiles: (start_zoom, end_zoom, pan_dx_frac, pan_dy_frac)
    moves = {
        "bloodstream":    (1.12, 1.28, 0.00,  0.04),   # slow push in
        "unhealthy_fat":  (1.20, 1.08, 0.02,  0.00),   # slow pull back
        "plaque_buildup": (1.10, 1.25, -0.03, 0.02),   # push + drift
        "sedentary":      (1.08, 1.18, 0.00, -0.03),   # subtle rise
        "diabetes":       (1.22, 1.35, 0.03,  0.03),   # push in aggressive
        "blood_pressure": (1.30, 1.10, 0.00,  0.00),   # pull back reveal
        "stress":         (1.15, 1.22, -0.02, 0.00),   # slow drift left
        "smoking_reveal": (1.05, 1.30, 0.00,  0.02),   # dramatic push
        "artery_damage":  (1.18, 1.28, 0.02, -0.02),   # diagonal push
    }
    z0, z1, dx_frac, dy_frac = moves.get(scene_id, (1.10, 1.22, 0.0, 0.0))

    frames = []
    arr = np.array(padded)

    for i in range(n_frames):
        t = i / max(n_frames - 1, 1)
        # Ease-in-out for smooth deceleration
        te = 3*t**2 - 2*t**3
        zoom = z0 + (z1 - z0) * te

        # Crop window size at current zoom
        cw = int(iw / zoom)
        ch = int(ih / zoom)

        # Center + pan offset
        cx = bw // 2 + int(dx_frac * bw * te)
        cy = bh // 2 + int(dy_frac * bh * te)

        x1 = max(0, cx - cw // 2)
        y1 = max(0, cy - ch // 2)
        x2 = min(bw, x1 + cw)
        y2 = min(bh, y1 + ch)
        # Clamp left/top
        x1 = max(0, x2 - cw)
        y1 = max(0, y2 - ch)

        crop = Image.fromarray(arr[y1:y2, x1:x2])
        frames.append(crop.resize((W, H), Image.LANCZOS))

    return frames

def animate_still(key: str, scene: dict, still: Image.Image, cache_dir: Path, i2v_model: str = I2V_MODEL) -> list:
    """Animate a still: tries WaveSpeed I2V, falls back to Ken Burns."""
    sid = scene["id"]
    clip_path = cache_dir / f"{sid}_clip.mp4"
    dur = scene["end"] - scene["start"]
    n_frames = int(dur * FPS)

    if clip_path.exists():
        print(f"  [{sid}] Loading cached clip", flush=True)
        return _load_video_frames_chunked(clip_path, n_frames)

    print(f"  [{sid}] Animating with {i2v_model}…", flush=True)
    num_frames_api = min(81, max(16, int(dur * 16)))
    still_480 = still.resize((480, 832), Image.LANCZOS)
    payload = {
        "image":                img_to_b64(still_480),
        "prompt":               scene["i2v_prompt"],
        "num_frames":           num_frames_api,
        "guidance_scale":       6.0,
        "num_inference_steps":  30,
    }
    try:
        task_id = _submit(key, i2v_model, payload)
        print(f"    Task ID: {task_id}", flush=True)
        url = _poll(key, task_id, timeout=900)
        tmp = _download(url, ".mp4")
        shutil.move(str(tmp), str(clip_path))
        print(f"    Clip saved → {clip_path}", flush=True)
        return _load_video_frames_chunked(clip_path, n_frames)
    except Exception as e:
        print(f"    I2V failed ({e}) — using cinematic Ken Burns", flush=True)
        return ken_burns(still, n_frames, sid)

# ─── MEMORY-SAFE VIDEO READER ─────────────────────────────────────────────────
def _load_video_frames_chunked(path: Path, target_count: int) -> list:
    """Load video frames, scaling to target_count, avoiding full-RAM load."""
    import imageio
    import imageio_ffmpeg
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()

    reader = imageio.get_reader(str(path))
    meta = reader.get_meta_data()
    src_fps = meta.get("fps", FPS)
    src_dur = meta.get("duration", target_count / FPS)
    src_count = max(1, int(src_fps * src_dur))

    frames = []
    for raw in reader:
        frames.append(Image.fromarray(raw).convert("RGB"))
    reader.close()

    if not frames:
        return [Image.new("RGB", (W, H), DARK)] * target_count

    # Resample to target_count
    result = []
    for i in range(target_count):
        src_i = int(i / target_count * len(frames))
        result.append(frames[min(src_i, len(frames) - 1)])
    return result

def _load_avatar_seekable(path: str) -> "AvatarSeeker":
    """Return an object that gives avatar frames by index without full RAM load."""
    return AvatarSeeker(path)

class AvatarSeeker:
    """Lazy avatar frame reader — loads all frames once, exposes by index."""
    def __init__(self, path: str):
        import imageio
        import imageio_ffmpeg
        os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
        reader = imageio.get_reader(path)
        meta = reader.get_meta_data()
        self.fps = meta.get("fps", 30)
        self.duration = meta.get("duration", 0)
        # Stream at reduced resolution to save memory
        self._frames = []
        for raw in reader:
            img = Image.fromarray(raw).convert("RGB")
            # Downsample to 640×360 max during loading
            if img.width > 640:
                img = img.resize((640, int(img.height * 640 / img.width)), Image.BILINEAR)
            self._frames.append(img)
        reader.close()
        self.n = len(self._frames)
        print(f"  Avatar: {self.n} frames @ {self.fps}fps = {self.n/self.fps:.1f}s")

    def at(self, t: float) -> Image.Image:
        idx = int(t * self.fps)
        return self._frames[min(idx, self.n - 1)]

# ─── AUDIO EXTRACTION ─────────────────────────────────────────────────────────
def extract_audio(video_path: str, out_path: Path) -> bool:
    """Extract audio track from avatar video."""
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    ret = os.system(f'"{ffmpeg}" -y -i "{video_path}" -vn -acodec aac -b:a 192k "{out_path}" -loglevel error')
    return ret == 0 and out_path.exists()

def merge_audio(video_path: str, audio_path: str, out_path: str) -> bool:
    """Merge audio into the final video."""
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = (
        f'"{ffmpeg}" -y -i "{video_path}" -i "{audio_path}" '
        f'-c:v copy -c:a aac -b:a 192k -shortest "{out_path}" -loglevel error'
    )
    return os.system(cmd) == 0

# ─── MAIN PIPELINE ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Dr. P Cinematic Medical Trailer Generator")
    parser.add_argument("--avatar",   default=AVATAR_PATH, help="Path to avatar video")
    parser.add_argument("--output",   default="drp_trailer.mp4")
    parser.add_argument("--api-key",  default=None)
    parser.add_argument("--cache-dir", default="./trailer_cache")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Skip API calls, use dark colour placeholders")
    parser.add_argument("--t2i-model", default=T2I_MODEL)
    parser.add_argument("--i2v-model", default=I2V_MODEL)
    parser.add_argument("--skip-i2v", action="store_true",
                        help="Use generated stills without animating (faster test)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("WAVESPEED_API_KEY", "")
    if not api_key and not args.dry_run:
        sys.exit("Error: WAVESPEED_API_KEY not set")

    t2i_model = args.t2i_model
    i2v_model = args.i2v_model

    cache = Path(args.cache_dir)
    cache.mkdir(exist_ok=True)

    # ── Load avatar (memory-safe) ──────────────────────────────────────────
    print("Loading avatar video…")
    avatar = AvatarSeeker(args.avatar)

    # ── Extract audio ──────────────────────────────────────────────────────
    audio_path = cache / "avatar_audio.aac"
    has_audio = False
    if not audio_path.exists():
        print("Extracting audio from avatar…")
        has_audio = extract_audio(args.avatar, audio_path)
    else:
        has_audio = True
    print(f"  Audio: {'extracted' if has_audio else 'unavailable'}")

    # ── Generate / load cinematic clips ──────────────────────────────────
    print("\nGenerating cinematic clips…")
    scene_frames: dict = {}   # scene_id → list[PIL.Image]

    for scene in SCENES:
        sid = scene["id"]
        if scene["t2i_prompt"] is None:
            scene_frames[sid] = None
            continue

        dur = scene["end"] - scene["start"]
        n = int(dur * FPS)

        if args.dry_run:
            colors = {
                "bloodstream": (40, 8, 8), "unhealthy_fat": (18, 12, 6),
                "plaque_buildup": (50, 14, 6), "sedentary": (8, 8, 14),
                "diabetes": (55, 12, 5), "blood_pressure": (65, 9, 7),
                "stress": (8, 8, 18), "smoking_reveal": (8, 6, 6),
                "artery_damage": (45, 10, 4),
            }
            placeholder = Image.new("RGB", (W, H), colors.get(sid, (14, 10, 8)))
            scene_frames[sid] = [placeholder] * n
            continue

        print(f"\n[{sid}]")
        still = generate_still(api_key, scene, cache, t2i_model)

        if args.skip_i2v:
            scene_frames[sid] = [still.copy()] * n
        else:
            scene_frames[sid] = animate_still(api_key, scene, still, cache, i2v_model)

    # ── Assemble final frame sequence ─────────────────────────────────────
    print("\nAssembling frames…")
    total_dur = max(s["end"] for s in SCENES) + 3.5   # +3.5s brand outro
    total_frames = int(total_dur * FPS)

    def active_scene(t: float):
        for s in reversed(SCENES):
            if s["start"] <= t:
                return s
        return SCENES[0]

    FADE = 0.45   # crossfade seconds
    video_out = cache / "raw_video.mp4"

    import imageio
    import imageio_ffmpeg
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()

    writer = imageio.get_writer(
        str(video_out), fps=FPS, codec="libx264", quality=9,
        ffmpeg_params=[
            "-preset", "slow", "-pix_fmt", "yuv420p",
            "-crf", "17", "-movflags", "+faststart", "-profile:v", "high",
        ],
        macro_block_size=1,
    )

    prev_frame: Image.Image = None
    prev_scene_id: str = None

    for fi in range(total_frames):
        t = fi / FPS
        scene = active_scene(t)
        sid = scene["id"]
        local_t = t - scene["start"]
        dur = scene["end"] - scene["start"]
        local_p = clamp(local_t / max(dur, 0.01))

        # Get avatar frame
        av = avatar.at(t)

        # Get cinematic frame
        cin_list = scene_frames.get(sid)
        cin_idx = int(local_t * FPS)
        cin = (cin_list[min(cin_idx, len(cin_list)-1)].copy()
               if cin_list else None)

        # Compose base
        mode = scene["avatar_mode"]
        base = avatar_to_portrait(av, mode, cin)

        # Colour grade + vignette
        base = apply_cinematic_grade(base)
        base = apply_vignette(base, 0.58 if mode == "cut" else 0.42)

        # Crossfade on scene change
        if prev_frame is not None and sid != prev_scene_id:
            fade_t = clamp(local_t / FADE)
            if fade_t < 1.0:
                base = crossfade(prev_frame, base, ease_in_out(fade_t))

        # ECG heartbeat line
        base = draw_heartbeat_line(base, t, alpha=95)

        # Brand outro (no text overlays on main content)
        outro_t = max(s["end"] for s in SCENES) + 0.5
        if t >= outro_t:
            prog = clamp((t - outro_t) / 3.0)
            base = draw_brand_outro(base, prog)

        writer.append_data(np.array(base))
        prev_frame = base
        prev_scene_id = sid

        if fi % (FPS * 5) == 0:
            print(f"  [{fi}/{total_frames}] {t:.1f}s / {total_dur:.1f}s", flush=True)

    writer.close()
    print(f"  Raw video → {video_out}")

    # ── Merge audio ───────────────────────────────────────────────────────
    final_out = args.output
    if has_audio:
        print(f"Merging audio into {final_out}…")
        ok = merge_audio(str(video_out), str(audio_path), final_out)
        if not ok:
            print("  Audio merge failed — copying raw video")
            shutil.copy(str(video_out), final_out)
    else:
        shutil.copy(str(video_out), final_out)

    size_mb = os.path.getsize(final_out) / 1024 / 1024
    print(f"\n✓ Done! {final_out}  ({size_mb:.1f} MB)")
    print("\nNext step — add soundtrack:")
    print(f"  python add_soundtrack.py --video {final_out}")


if __name__ == "__main__":
    main()
