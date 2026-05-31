"""
WaveSpeed model finder — run this on Termux to find the exact slug
for any model before using it in cinematic_trailer.py.

Usage:
    python find_model.py banana
    python find_model.py wan
    python find_model.py flux
"""
import os, sys, requests
from pathlib import Path

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

search = sys.argv[1].lower() if len(sys.argv) > 1 else ""

# Try to list models
r = requests.get("https://api.wavespeed.ai/api/v2/models",
                 headers={"Authorization": f"Bearer {key}"}, timeout=15)

if r.status_code == 200:
    models = r.json().get("data", r.json())
    found = [m for m in models
             if search in str(m).lower()] if search else models
    if not found:
        print(f"No models matching '{search}'")
    for m in found:
        print(m)
else:
    print(f"Models endpoint returned {r.status_code}: {r.text[:200]}")
    print()
    print("Trying common slug patterns for:", search)
    slugs = [
        f"wavespeed-ai/{search}",
        f"wavespeed-ai/{search.replace(' ','-')}",
        f"google/{search.replace(' ','-')}",
        f"wavespeed-ai/nano-banana-2-edit",
        f"wavespeed-ai/nano-banana2-edit",
        f"wavespeed-ai/nano-banana-pro",
    ]
    for slug in slugs:
        resp = requests.post(
            f"https://api.wavespeed.ai/api/v2/{slug}",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"prompt": "test", "size": "720*1280"},
            timeout=10,
        )
        status = "✅ FOUND" if resp.status_code in (200, 201, 202) else f"❌ {resp.status_code}"
        print(f"  {status}  {slug}  |  {resp.text[:80]}")
