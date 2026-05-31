"""
Dr. P's Corner — Cinematic Medical Trailer Generator
=====================================================
Transforms the avatar talking video into a Netflix-style medical
documentary trailer using WaveSpeed Nano Banana Pro (T2I) + Wan 2.1 (I2V).

Pipeline:
  1. Generate cinematic stills for each scene  (WaveSpeed T2I)
  2. Animate each still into a video clip      (WaveSpeed I2V)
  3. Process avatar video → 9:16 portrait
  4. Assemble scenes with transitions + PiP
  5. Apply motion-graphics text overlays
  6. Apply cinematic color grading
  7. Export 1080×1920 @ 24fps

Usage (run on your local machine / Termux):
    python cinematic_trailer.py \
        --avatar /path/to/VID20260531WA0016.mp4 \
        --output drp_trailer.mp4

Environment:
    WAVESPEED_API_KEY=wsk_live_...
"""

import argparse
import base64
import math
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ─── CONFIG ───────────────────────────────────────────────────────────────────
W, H = 1080, 1920
FPS = 24
WAVESPEED_BASE = "https://api.wavespeed.ai/api/v2"

T2I_MODEL = "wavespeed-ai/nano-banana-2-edit"      # Google Nano Banana 2 Edit — hyper-realistic stills
I2V_MODEL = "wavespeed-ai/wan2.1-i2v-480p"        # Wan 2.1 — animate the stills

# Load .env if present
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
DARK       = ( 12,   8,   6)
MID_DARK   = ( 28,  18,  12)
BLOOD_RED  = (180,  30,  20)
AMBER      = (220, 140,  60)

# ─── SCENE DEFINITIONS ────────────────────────────────────────────────────────
# (start_sec, end_sec, avatar_mode, text_overlay, t2i_prompt, i2v_prompt)
# avatar_mode: "full" | "pip" | "cut" (cut = cinematic only, no avatar)
SCENES = [
    {
        "id": "intro",
        "start": 0.0, "end": 4.0,
        "avatar_mode": "full",
        "text": None,
        "t2i_prompt": None,   # no cutaway — avatar only
    },
    {
        "id": "bloodstream",
        "start": 3.5, "end": 8.5,
        "avatar_mode": "cut",
        "text": "Your habits are shaping\nyour blood vessels.",
        "t2i_prompt": (
            "Extreme macro cinematic interior of a human blood vessel tunnel, "
            "dark deep-red walls glistening, thousands of red blood cells drifting "
            "in viscous fluid, bioluminescent particles floating, volumetric god rays "
            "penetrating darkness, amber and crimson tones, 9:16 vertical portrait, "
            "photorealistic, 8K, shallow depth of field, film grain, cinematic"
        ),
        "i2v_prompt": (
            "Slow cinematic push through blood vessel tunnel, particles drifting, "
            "subtle pulse and flow, god rays shifting, atmospheric depth"
        ),
    },
    {
        "id": "unhealthy_fat",
        "start": 8.5, "end": 14.0,
        "avatar_mode": "pip",
        "text": "Excess unhealthy fat\nbuilds up slowly.",
        "t2i_prompt": (
            "Hyper-realistic cinematic macro close-up of greasy fast food floating "
            "in deep darkness — glistening burger, oily fries, sugary drink with condensation, "
            "fat droplets refracting dramatic side-lighting, oil sheen on surfaces, "
            "microscopic fat particles visible in foreground air, dark premium moody aesthetic, "
            "9:16 vertical portrait, photorealistic, 8K, cinematic lens flare, deep shadows"
        ),
        "i2v_prompt": (
            "Slow cinematic reveal of fast food in darkness, fat particles drifting forward, "
            "dramatic side-lighting shifts, macro close-up details emerge, moody and heavy"
        ),
    },
    {
        "id": "plaque_buildup",
        "start": 12.0, "end": 16.0,
        "avatar_mode": "cut",
        "text": "Cholesterol. Plaque.\nSlowing blood flow.",
        "t2i_prompt": (
            "Cinematic medical visualization: interior cross-section of a human artery, "
            "yellowish cholesterol plaque clinging to reddish vessel walls, blood flow "
            "visibly narrowed, sticky fat deposits building on artery surface, "
            "dark atmospheric medical aesthetic, amber and dark crimson palette, "
            "9:16 vertical portrait, photorealistic, 8K, volumetric depth"
        ),
        "i2v_prompt": (
            "Slow push through narrowing artery, plaque slowly building on walls, "
            "blood flow becoming sluggish, dark cinematic medical atmosphere"
        ),
    },
    {
        "id": "sedentary",
        "start": 14.5, "end": 19.0,
        "avatar_mode": "pip",
        "text": "Movement keeps\nblood flowing.",
        "t2i_prompt": (
            "Cinematic dark portrait silhouette: person sitting completely still in a "
            "dim room for hours, hunched posture, head drooping, single harsh rim light "
            "from the side, deep shadows consuming 80% of frame, heavy oppressive mood, "
            "atmospheric haze, chair barely visible, film noir medical aesthetic, "
            "9:16 vertical portrait, photorealistic, 8K, grain, shallow depth of field"
        ),
        "i2v_prompt": (
            "Slow cinematic camera circle around sedentary silhouette, light slowly "
            "dimming, heavy atmospheric haze thickening, emotional stillness"
        ),
    },
    {
        "id": "diabetes",
        "start": 19.0, "end": 23.5,
        "avatar_mode": "cut",
        "text": "High sugar silently\ndamages vessels.",
        "t2i_prompt": (
            "Extreme macro cinematic shot inside a human blood vessel: sharp crystalline "
            "glucose particles flowing aggressively through dark blood, artery lining "
            "showing inflammation — subtle orange-red inflammatory glow on vessel walls, "
            "tiny micro-tears beginning, medical biopunk aesthetic, dark crimson and amber "
            "tones with fiery inflammatory highlights, 9:16 vertical portrait, "
            "photorealistic, 8K, cinematic depth"
        ),
        "i2v_prompt": (
            "Glucose crystals flowing through blood vessel, inflammatory glow pulsing "
            "on artery walls, slow cinematic push through damaged vessel interior"
        ),
    },
    {
        "id": "blood_pressure",
        "start": 23.5, "end": 27.5,
        "avatar_mode": "pip",
        "text": "Pressure weakens\nthe vessels.",
        "t2i_prompt": (
            "Cinematic macro shot of a human artery under extreme hypertensive pressure: "
            "vessel walls bulging dramatically, blood surging violently with visible "
            "pressure waves slamming vessel walls, white pressure flares at impact points, "
            "deep dark red with stark white highlights, walls visibly straining, "
            "slow-motion freeze-frame energy, 9:16 vertical portrait, photorealistic, "
            "8K, cinematic impact, dramatic contrast"
        ),
        "i2v_prompt": (
            "Blood pressure waves slamming artery walls in slow motion, vessel bulging "
            "and recoiling rhythmically, dramatic cinematic impact, deep heartbeat pulse"
        ),
    },
    {
        "id": "stress",
        "start": 27.0, "end": 31.5,
        "avatar_mode": "cut",
        "text": "Stress affects\nthe body too.",
        "t2i_prompt": (
            "Cinematic dark atmospheric portrait: emotionally drained silhouette in a "
            "very dark room, face faintly illuminated by cold phone screen glow, dark "
            "smoke wisps rising and curling around the figure, irregular glowing particles "
            "representing cortisol and adrenaline drifting through air, heavy oppressive "
            "mood, barely visible surroundings, emotional weight, 9:16 vertical portrait, "
            "photorealistic, 8K, grain, cinematic shallow focus"
        ),
        "i2v_prompt": (
            "Dark smoke slowly expanding around stressed silhouette, particles drifting, "
            "phone light flickering slightly, atmosphere becoming heavier and more oppressive"
        ),
    },
    {
        "id": "smoking_reveal",
        "start": 30.5, "end": 34.5,
        "avatar_mode": "pip",
        "text": "Smoking destroys\nblood vessels.",
        "t2i_prompt": (
            "DRAMATIC cinematic reveal: dark silhouette smoking, cigarette ember burning "
            "intensely bright in near-total darkness, thick white-grey smoke billowing "
            "and expanding dramatically to fill entire frame, smoke tendrils morphing at "
            "edges into microscopic damaged blood vessel structures — darkened, narrowed, "
            "necrotic, deep charcoal and near-black tones with glowing ember as only light "
            "source, cinematic impact composition, 9:16 vertical portrait, photorealistic, "
            "8K, extreme atmosphere, film grain"
        ),
        "i2v_prompt": (
            "Slow dramatic reveal: smoke expanding to fill frame, ember glowing, "
            "smoke morphing into damaged blood vessels at edges, cinematic impact, "
            "slow-motion, very atmospheric"
        ),
    },
    {
        "id": "artery_damage",
        "start": 33.5, "end": 38.0,
        "avatar_mode": "cut",
        "text": "Damage builds\nover time.",
        "t2i_prompt": (
            "Extreme macro cinematic sequence: human artery interior showing progressive "
            "damage — left half healthy (bright red, open, clean walls), right half "
            "severely diseased (dark, narrowed, thick black-brown plaque coating walls, "
            "tiny white blood clot forming at narrowest point), blood flow nearly blocked, "
            "dramatic contrast between healthy and damaged, dark medical documentary aesthetic, "
            "9:16 vertical portrait, photorealistic, 8K, cinematic"
        ),
        "i2v_prompt": (
            "Healthy artery rapidly transforming to blocked vessel, plaque accelerating, "
            "blood flow stopping, tiny clot forming in slow cinematic motion"
        ),
    },
    {
        "id": "outro",
        "start": 36.5, "end": 41.0,
        "avatar_mode": "full",
        "text": "Your daily habits matter\nmore than you think.",
        "t2i_prompt": None,   # avatar holds screen for outro
    },
]

# ─── FONT FALLBACKS ───────────────────────────────────────────────────────────
FONT_PATHS = {
    "serif": [
        "/root/.fonts/PlayfairDisplay-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/system/fonts/NotoSerif-Bold.ttf",
        "/data/data/com.termux/files/usr/share/fonts/liberation/LiberationSerif-Bold.ttf",
    ],
    "sans": [
        "/root/.fonts/DMSans-Medium.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/system/fonts/Roboto-Regular.ttf",
        "/data/data/com.termux/files/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
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

# ─── COLOR GRADING ────────────────────────────────────────────────────────────
def apply_cinematic_grade(img: Image.Image) -> Image.Image:
    """
    Dark cinematic grade:
    - Crush shadows to near-black
    - Lift blacks slightly (film look)
    - Boost contrast in midtones
    - Add warm shadow tint (brown/amber)
    - Add subtle cool highlight tint (lilac)
    - Reduce saturation slightly
    - Add film grain
    """
    arr = np.array(img).astype(np.float32)

    # Exposure: slightly underexpose for drama
    arr *= 0.88

    # Contrast S-curve
    arr = arr / 255.0
    arr = arr ** 0.9  # slight gamma adjustment
    # S-curve: lift shadows, crush highlights
    arr = 0.5 * np.sin(np.pi * (arr - 0.5)) + 0.5
    arr = arr * 255.0

    # Shadow tint — warm amber/brown in darks
    luma = arr.mean(axis=2)   # (H, W)
    shadow_mask = np.clip(1.0 - luma / 120.0, 0, 1)[:, :, np.newaxis]  # (H,W,1)
    arr[:, :, 0:1] += shadow_mask * 12   # R
    arr[:, :, 1:2] += shadow_mask * 4    # G
    arr[:, :, 2:3] -= shadow_mask * 8    # B

    # Highlight tint — subtle lilac in brights
    hi_mask = np.clip((luma - 180.0) / 75.0, 0, 1)[:, :, np.newaxis]
    arr[:, :, 0:1] += hi_mask * 8
    arr[:, :, 1:2] += hi_mask * 2
    arr[:, :, 2:3] += hi_mask * 14

    # Crush blacks
    arr = np.maximum(arr - 8, 0)

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img_graded = Image.fromarray(arr)

    # Desaturate slightly
    from PIL import ImageEnhance
    img_graded = ImageEnhance.Color(img_graded).enhance(0.82)

    # Film grain
    grain = np.random.randint(-14, 15, arr.shape, dtype=np.int16)
    arr2 = np.clip(np.array(img_graded).astype(np.int16) + grain, 0, 255).astype(np.uint8)

    return Image.fromarray(arr2)

def apply_vignette(img: Image.Image, strength: float = 0.6) -> Image.Image:
    """Add a strong cinematic vignette."""
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vig)
    for i in range(60):
        r = W // 2 + int(i * 12)
        alpha = int(strength * 255 * (i / 60) ** 2)
        color = (0, 0, 0, min(alpha, 255))
        draw.ellipse([W//2 - r, H//2 - r*2, W//2 + r, H//2 + r*2], outline=color, width=18)
    vignette = vig.filter(ImageFilter.GaussianBlur(30))
    base = img.convert("RGBA")
    return Image.alpha_composite(base, vignette).convert("RGB")

# ─── AVATAR FRAME PROCESSOR ───────────────────────────────────────────────────
def avatar_to_portrait(frame: Image.Image, mode: str = "full",
                        bg_frames: list = None, bg_idx: int = 0) -> Image.Image:
    """
    Convert landscape avatar frame (640×360) to 9:16 portrait (1080×1920).

    mode 'full' : blur-fill bg + centred avatar
    mode 'pip'  : avatar in bottom-right corner, bg fills frame
    """
    iw, ih = frame.size

    if mode == "full":
        # Scale avatar to fill full width
        scale = W / iw
        aw = W
        ah = int(ih * scale)
        avatar_scaled = frame.resize((aw, ah), Image.LANCZOS)

        # Blurred + darkened full-frame background
        bg_scale = H / ih
        bw = int(iw * bg_scale)
        bg = frame.resize((bw, H), Image.LANCZOS)
        if bw > W:
            ox = (bw - W) // 2
            bg = bg.crop((ox, 0, ox + W, H))
        else:
            pad = Image.new("RGB", (W, H), (0, 0, 0))
            pad.paste(bg, ((W - bw) // 2, 0))
            bg = pad

        bg = bg.filter(ImageFilter.GaussianBlur(25))
        bg = Image.blend(bg, Image.new("RGB", (W, H), DARK), 0.55)

        # Composite avatar centred vertically
        ay = (H - ah) // 2
        bg.paste(avatar_scaled, (0, ay))
        return bg

    elif mode == "pip":
        # bg is the cinematic clip frame
        if bg_frames and bg_idx < len(bg_frames):
            base = bg_frames[bg_idx].copy()
        else:
            base = Image.new("RGB", (W, H), DARK)
        base = base.resize((W, H), Image.LANCZOS)

        # PiP: avatar in lower-right corner, 35% of frame width
        pip_w = int(W * 0.38)
        pip_h = int(pip_w * ih / iw)
        pip = frame.resize((pip_w, pip_h), Image.LANCZOS)

        # Dark semi-transparent border
        border = 6
        pip_with_border = Image.new("RGB", (pip_w + border*2, pip_h + border*2), (20, 12, 8))
        pip_with_border.paste(pip, (border, border))

        px = W - pip_w - border*2 - 40
        py = H - pip_h - border*2 - 120
        base.paste(pip_with_border, (px, py))

        # Subtle shadow behind pip
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rectangle([px-20, py-20, px+pip_w+border*2+20, py+pip_h+border*2+20],
                     fill=(0, 0, 0, 80))
        shadow = shadow.filter(ImageFilter.GaussianBlur(15))
        base = Image.alpha_composite(base.convert("RGBA"), shadow).convert("RGB")
        base.paste(pip_with_border, (px, py))
        return base

    return frame

# ─── MOTION GRAPHICS ──────────────────────────────────────────────────────────
def draw_text_overlay(img: Image.Image, text: str,
                      progress: float, position: str = "lower") -> Image.Image:
    """
    Minimal cinematic text overlay. Fades in from bottom.
    progress 0→1 controls opacity + slide.
    """
    if not text or progress <= 0:
        return img

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    lines = text.strip().split("\n")
    fnt = font("sans", 52)
    line_h = 66
    total_h = len(lines) * line_h

    if position == "lower":
        base_y = H - 260
    else:
        base_y = 220

    alpha = int(240 * ease_out(progress))
    slide = int((1 - ease_out(progress)) * 30)

    for i, line in enumerate(lines):
        bb = fnt.getbbox(line)
        tw = bb[2] - bb[0]
        x = (W - tw) // 2
        y = base_y - total_h + i * line_h + slide

        # Shadow
        d.text((x + 2, y + 2), line, font=fnt, fill=(0, 0, 0, int(alpha * 0.6)))
        # Main text
        d.text((x, y), line, font=fnt, fill=(*CREAM, alpha))

    # Thin separator line above text
    if progress > 0.5:
        line_alpha = int(180 * ease_out((progress - 0.5) * 2))
        sep_y = base_y - total_h - 20 + slide
        d.line([(W//2 - 80, sep_y), (W//2 + 80, sep_y)],
               fill=(*SOFT_PINK, line_alpha), width=2)

    base = img.convert("RGBA")
    return Image.alpha_composite(base, layer).convert("RGB")

def draw_heartbeat_line(img: Image.Image, t: float, alpha: int = 160) -> Image.Image:
    """Subtle ECG heartbeat line at bottom of frame."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y_base = H - 60
    pts = []
    for x in range(0, W, 4):
        phase = (x / W + t * 0.5) * math.pi * 6
        blip_phase = (x / W + t * 0.3) % 1.0
        if 0.45 < blip_phase < 0.55:
            amp = int(80 * math.sin((blip_phase - 0.45) / 0.1 * math.pi))
        else:
            amp = int(4 * math.sin(phase))
        pts.append((x, y_base - amp))
    if len(pts) > 1:
        for i in range(len(pts) - 1):
            d.line([pts[i], pts[i+1]], fill=(*DEEP_ROSE, alpha), width=2)
    base = img.convert("RGBA")
    return Image.alpha_composite(base, layer).convert("RGB")

def draw_brand_outro(img: Image.Image, progress: float) -> Image.Image:
    """Final brand card fade-in."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = int(255 * ease_out(progress))

    # Dark overlay
    d.rectangle([0, 0, W, H], fill=(8, 5, 3, int(180 * ease_out(progress))))

    if progress > 0.3:
        fa = int(255 * ease_out((progress - 0.3) / 0.7))
        fn1 = font("serif", 72)
        fn2 = font("sans", 38)
        bb1 = fn1.getbbox("Dr. P's Corner")
        bb2 = fn2.getbbox("Health Without The Complexity")
        d.text(((W - (bb1[2]-bb1[0])) // 2, H//2 - 60),
               "Dr. P's Corner", font=fn1, fill=(*CREAM, fa))
        d.text(((W - (bb2[2]-bb2[0])) // 2, H//2 + 40),
               "Health Without The Complexity", font=fn2, fill=(*SOFT_PINK, fa))
        # Separator
        d.line([(W//2 - 140, H//2 + 20), (W//2 + 140, H//2 + 20)],
               fill=(*NUDE_BROWN, int(fa * 0.6)), width=2)

    base = img.convert("RGBA")
    return Image.alpha_composite(base, layer).convert("RGB")

def crossfade(frame_a: Image.Image, frame_b: Image.Image, t: float) -> Image.Image:
    t = clamp(t)
    if t <= 0:
        return frame_a
    if t >= 1:
        return frame_b
    return Image.blend(frame_a.convert("RGB"), frame_b.convert("RGB"), t)

# ─── WAVESPEED API ────────────────────────────────────────────────────────────
def ws_headers(key: str) -> dict:
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

def img_to_b64(img: Image.Image) -> str:
    import io as _io
    buf = _io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def file_to_b64(path: str) -> str:
    ext = Path(path).suffix.lstrip(".").lower()
    mime = "jpeg" if ext in ("jpg","jpeg") else "png"
    with open(path, "rb") as f:
        return f"data:image/{mime};base64," + base64.b64encode(f.read()).decode()

def poll(key: str, task_id: str, timeout: int = 600) -> str:
    deadline = time.time() + timeout
    interval = 4
    while time.time() < deadline:
        r = requests.get(f"{WAVESPEED_BASE}/predictions/{task_id}/fetch",
                         headers=ws_headers(key), timeout=20)
        r.raise_for_status()
        data = r.json()["data"]
        status = data.get("status", "")
        print(f"    [{task_id[:10]}] {status}", flush=True)
        if status == "completed":
            out = data.get("outputs", [])
            if out:
                return out[0]
            raise RuntimeError("Completed but no outputs")
        if status in ("failed", "cancelled"):
            raise RuntimeError(f"Task {status}: {data.get('error')}")
        time.sleep(interval)
        interval = min(interval * 1.2, 12)
    raise TimeoutError("Task timed out")

def generate_image(key: str, prompt: str, model: str = T2I_MODEL,
                   size: str = "720*1280") -> Image.Image:
    """Generate a cinematic still via WaveSpeed T2I."""
    payload = {
        "prompt": prompt,
        "size": size,
        "num_inference_steps": 30,
        "guidance_scale": 7.5,
    }
    r = requests.post(f"{WAVESPEED_BASE}/{model}",
                      headers=ws_headers(key), json=payload, timeout=60)
    r.raise_for_status()
    task_id = r.json()["data"]["id"]
    url = poll(key, task_id)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    urllib.request.urlretrieve(url, tmp.name)
    img = Image.open(tmp.name).convert("RGB")
    os.unlink(tmp.name)
    return img

def animate_image(key: str, img: Image.Image, prompt: str,
                  duration_sec: int = 4, model: str = I2V_MODEL) -> Path:
    """Animate a still image into a video clip via WaveSpeed I2V."""
    num_frames = min(81, max(16, duration_sec * 16))
    payload = {
        "image": img_to_b64(img),
        "prompt": prompt,
        "num_frames": num_frames,
        "guidance_scale": 6.0,
        "num_inference_steps": 30,
    }
    r = requests.post(f"{WAVESPEED_BASE}/{model}",
                      headers=ws_headers(key), json=payload, timeout=60)
    r.raise_for_status()
    task_id = r.json()["data"]["id"]
    url = poll(key, task_id)
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    urllib.request.urlretrieve(url, tmp.name)
    return Path(tmp.name)

# ─── VIDEO READER ─────────────────────────────────────────────────────────────
def load_video_frames(path: str, target_fps: int = FPS) -> list:
    """Load all frames from a video, resampled to target_fps."""
    import imageio
    reader = imageio.get_reader(str(path))
    meta = reader.get_meta_data()
    src_fps = meta.get("fps", 30)
    raw = [Image.fromarray(f).convert("RGB") for f in reader]
    reader.close()

    if abs(src_fps - target_fps) < 0.5:
        return raw

    # Simple linear resampling
    duration = len(raw) / src_fps
    n_out = int(duration * target_fps)
    out = []
    for i in range(n_out):
        src_i = int(i / target_fps * src_fps)
        out.append(raw[min(src_i, len(raw)-1)])
    return out

def extend_frames(frames: list, n: int) -> list:
    if not frames:
        return [Image.new("RGB", (W, H), DARK)] * n
    result = []
    while len(result) < n:
        result.extend(frames)
    return result[:n]

# ─── MAIN PIPELINE ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Dr. P Cinematic Trailer Generator")
    parser.add_argument("--avatar", required=True, help="Path to avatar video (.mp4)")
    parser.add_argument("--output", default="drp_trailer.mp4", help="Output path")
    parser.add_argument("--api-key", default=None, help="WaveSpeed API key")
    parser.add_argument("--cache-dir", default="./trailer_cache",
                        help="Directory to cache generated clips (avoids re-generation)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip API calls, use solid colour placeholders")
    parser.add_argument("--t2i-model", default=T2I_MODEL,
                        help=f"WaveSpeed T2I model (default: {T2I_MODEL})")
    parser.add_argument("--i2v-model", default=I2V_MODEL,
                        help=f"WaveSpeed I2V model (default: {I2V_MODEL})")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("WAVESPEED_API_KEY", "")
    if not api_key and not args.dry_run:
        sys.exit("Error: provide --api-key or WAVESPEED_API_KEY in .env")

    cache = Path(args.cache_dir)
    cache.mkdir(exist_ok=True)

    # ── Load avatar video ──────────────────────────────────────────────────
    print("Loading avatar video…")
    avatar_frames = load_video_frames(args.avatar, FPS)
    avatar_duration = len(avatar_frames) / FPS
    print(f"  {len(avatar_frames)} frames @ {FPS}fps = {avatar_duration:.1f}s")

    # ── Generate / load cinematic clips ──────────────────────────────────
    scene_clips: dict = {}   # scene_id → list of PIL frames (1080×1920)

    for scene in SCENES:
        sid = scene["id"]
        if scene["t2i_prompt"] is None:
            scene_clips[sid] = None   # avatar-only scene
            continue

        dur = scene["end"] - scene["start"]
        n_frames = int(dur * FPS)

        clip_path = cache / f"{sid}_clip.mp4"
        still_path = cache / f"{sid}_still.png"

        if clip_path.exists():
            print(f"[{sid}] Loading cached clip…")
            raw = load_video_frames(str(clip_path), FPS)
            scene_clips[sid] = extend_frames(raw, n_frames)
            continue

        if args.dry_run:
            print(f"[{sid}] Dry-run placeholder")
            placeholder = Image.new("RGB", (W, H), (18, 10, 6))
            scene_clips[sid] = [placeholder] * n_frames
            continue

        print(f"[{sid}] Generating still with {args.t2i_model}…")
        if still_path.exists():
            still = Image.open(still_path).convert("RGB")
        else:
            still = generate_image(api_key, scene["t2i_prompt"],
                                   model=args.t2i_model, size="720*1280")
            still = still.resize((W, H), Image.LANCZOS)
            still.save(still_path)
            print(f"  Still saved → {still_path}")

        print(f"[{sid}] Animating with {args.i2v_model}…")
        anim_path = animate_image(api_key, still,
                                  scene.get("i2v_prompt", scene["t2i_prompt"]),
                                  duration_sec=max(3, int(dur)),
                                  model=args.i2v_model)
        # Save to cache
        import shutil
        shutil.move(str(anim_path), str(clip_path))
        print(f"  Clip saved → {clip_path}")

        raw = load_video_frames(str(clip_path), FPS)
        scene_clips[sid] = extend_frames(raw, n_frames)

    # ── Build final frame sequence ────────────────────────────────────────
    print("\nAssembling frames…")
    total_dur = max(s["end"] for s in SCENES) + 3.0  # +3s for outro fade
    total_frames = int(total_dur * FPS)
    all_frames: list = []

    # Pre-build a lookup: for each global frame, which scene are we in?
    def get_scene_at(t: float):
        active = [s for s in SCENES if s["start"] <= t < s["end"] + 0.5]
        return active[-1] if active else SCENES[-1]

    FADE_DUR = 0.5   # crossfade seconds between scenes
    prev_frame: Image.Image = None
    last_scene_id: str = None

    for fi in range(total_frames):
        t = fi / FPS
        scene = get_scene_at(t)
        sid = scene["id"]
        dur = scene["end"] - scene["start"]
        local_t = t - scene["start"]
        local_progress = clamp(local_t / dur)

        # ── Build base frame ──────────────────────────────────────────────
        av_idx = min(int(t * FPS), len(avatar_frames) - 1)
        av_frame = avatar_frames[av_idx]

        cin_frames = scene_clips.get(sid)
        cin_idx = int(local_t * FPS) if cin_frames else 0

        if scene["avatar_mode"] == "full" or cin_frames is None:
            base = avatar_to_portrait(av_frame, "full")
        elif scene["avatar_mode"] == "pip":
            pip_frames = cin_frames
            pip_frame = pip_frames[min(cin_idx, len(pip_frames)-1)] if pip_frames else None
            if pip_frame:
                pip_frame = pip_frame.resize((W, H), Image.LANCZOS)
            base = avatar_to_portrait(av_frame, "pip",
                                      bg_frames=[pip_frame] if pip_frame else None,
                                      bg_idx=0)
        else:  # "cut" — cinematic only
            cin_f = cin_frames[min(cin_idx, len(cin_frames)-1)]
            base = cin_f.resize((W, H), Image.LANCZOS)

        # ── Colour grade ──────────────────────────────────────────────────
        base = apply_cinematic_grade(base)
        base = apply_vignette(base, 0.55 if scene["avatar_mode"] == "cut" else 0.4)

        # ── Scene crossfade ───────────────────────────────────────────────
        if last_scene_id != sid and prev_frame is not None:
            # Cross-fade the transition
            fade_frames_count = int(FADE_DUR * FPS)
            fi_in_fade = 0
        if prev_frame is not None and last_scene_id != sid:
            fi_in_fade = 0
        # track fade within first FADE_DUR of a new scene
        fade_t = clamp(local_t / FADE_DUR) if local_t < FADE_DUR and prev_frame is not None else 1.0
        if fade_t < 1.0:
            base = crossfade(prev_frame, base, ease_in_out(fade_t))

        # ── Heartbeat line ────────────────────────────────────────────────
        base = draw_heartbeat_line(base, t, alpha=100)

        # ── Text overlay ─────────────────────────────────────────────────
        if scene["text"]:
            text_in  = clamp(local_t / 1.2)
            text_out = clamp((dur - local_t) / 0.6)
            text_prog = min(text_in, text_out)
            base = draw_text_overlay(base, scene["text"], text_prog)

        # ── Outro brand card ──────────────────────────────────────────────
        outro_start = max(s["end"] for s in SCENES) + 0.5
        if t >= outro_start:
            outro_prog = clamp((t - outro_start) / 2.5)
            base = draw_brand_outro(base, outro_prog)

        all_frames.append(base)
        prev_frame = base
        last_scene_id = sid

        if fi % (FPS * 5) == 0:
            print(f"  [{fi}/{total_frames}] {t:.1f}s / {total_dur:.1f}s", flush=True)

    # ── Encode video ──────────────────────────────────────────────────────
    print(f"\nEncoding {len(all_frames)} frames → {args.output}")
    import imageio
    import imageio_ffmpeg
    import os as _os
    _os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()

    writer = imageio.get_writer(
        args.output,
        fps=FPS,
        codec="libx264",
        quality=9,
        ffmpeg_params=[
            "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-movflags", "+faststart",
            "-profile:v", "high",
        ],
        macro_block_size=1,
    )
    for frame in all_frames:
        writer.append_data(np.array(frame))
    writer.close()

    size_mb = os.path.getsize(args.output) / 1024 / 1024
    print(f"\n✓ Done!  {args.output}  ({size_mb:.1f} MB)")
    print("\nNext steps:")
    print("  • Add soundtrack:  python add_soundtrack.py --video drp_trailer.mp4")
    print("  • Verify WaveSpeed model names if any 404 errors occur:")
    print(f"    T2I model used: {args.t2i_model}")
    print(f"    I2V model used: {args.i2v_model}")
    print("  • Check model names at: https://wavespeed.ai/models")


if __name__ == "__main__":
    main()
