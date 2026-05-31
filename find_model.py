"""
WaveSpeed model finder — run on Termux to find the exact model slug.
Tries every plausible variation and reports which ones work.

Usage:
    python find_model.py
"""
import os, sys
from pathlib import Path

# Load .env
_env = Path(__file__).parent / ".env"
if _env.exists():
    for _l in _env.read_text().splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _, _v = _l.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

key = os.environ.get("WAVESPEED_API_KEY", "")
if not key:
    sys.exit("Set WAVESPEED_API_KEY in .env")

import wavespeed
client = wavespeed.Client(api_key=key)

TEST_PROMPT = "cinematic dark artery, photorealistic"
TEST_INPUT  = {"prompt": TEST_PROMPT, "size": "480*832", "num_inference_steps": 1}

# Every plausible slug for "Google Nano Banana 2 Edit"
CANDIDATES = [
    # Nano Banana variations
    "wavespeed-ai/nano-banana-2-edit",
    "wavespeed-ai/nano-banana-2",
    "wavespeed-ai/nano-banana-pro",
    "wavespeed-ai/nano-banana",
    "wavespeed-ai/nano-banana-edit",
    # Google-namespaced
    "google/nano-banana-2-edit",
    "google/nano-banana-2",
    "google/nano-banana",
    # Other likely T2I models on WaveSpeed
    "wavespeed-ai/z-image/turbo",
    "wavespeed-ai/flux-dev",
    "wavespeed-ai/flux-schnell",
    "wavespeed-ai/flux-dev-fp8",
    "wavespeed-ai/stable-diffusion-v3-medium",
    "wavespeed-ai/wan2.1-t2v-480p",
]

print(f"Testing {len(CANDIDATES)} model slugs...\n")
found = []

for slug in CANDIDATES:
    try:
        out = client.run(slug, TEST_INPUT, timeout=60)
        print(f"  ✅  {slug}")
        found.append(slug)
    except Exception as e:
        msg = str(e)
        if "not found" in msg.lower() or "404" in msg:
            print(f"  ❌  {slug}  (not found)")
        elif "invalid" in msg.lower() or "400" in msg:
            print(f"  ⚠️   {slug}  (invalid input — model EXISTS, check params)")
            found.append(slug)
        else:
            print(f"  ✗   {slug}  ({msg[:80]})")

print()
if found:
    print("Found working models:")
    for s in found:
        print(f"  {s}")
    print(f"\nUse in trailer:  python cinematic_trailer.py --avatar VIDEO.mp4 --t2i-model {found[0]}")
else:
    print("No working T2I models found.")
    print("Check https://wavespeed.ai/models for your account's available models.")
    print("Then run:  python cinematic_trailer.py --t2i-model YOUR/MODEL-SLUG ...")
