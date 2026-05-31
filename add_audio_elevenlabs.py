"""
Dr. P's Corner — ElevenLabs Audio Generator
Generates the full narration voiceover and merges it with the video.

Usage:
    python add_audio_elevenlabs.py --video drp_wavespeed.mp4 --output drp_final.mp4
    python add_audio_elevenlabs.py --audio-only --output narration.mp3

Environment:
    ELEVENLABS_API_KEY  — ElevenLabs API key (or use --api-key arg)
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

# Load .env if present
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# ─── NARRATION SCRIPT ─────────────────────────────────────────────────────────
# Full word-for-word script matching the motion graphics timestamps.
# Adjust timing gaps via the <break> tags or by splitting into segments.
FULL_SCRIPT = """\
Dear girls… and dear mothers…

Periods are not dirty.
They are not shameful.
They are not a punishment for being a woman.

That little girl hiding her pad in school?
She deserves confidence.

That teenager scared because of stains?
She deserves support.

That mother silently enduring painful periods every month?
You deserve care too.

Today, let's stop whispering about menstruation like it's a secret.
Talk to your daughters.
Teach them without fear.
Without shame.

Because menstrual hygiene is not luxury.
It's dignity.
And here at Dr. P's Corner,
we believe every girl deserves health without the complexity.

Happy World Menstrual Hygiene Day.
Health. Dignity. Care.
"""

# ─── CONFIG ───────────────────────────────────────────────────────────────────
ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"

# Recommended voices for a warm, professional African/Black woman:
#   "Rachel"  — 21m00Tcm4TlvDq8ikWAM  (warm, American English)
#   "Domi"    — AZnzlk1XvdvUeBnXmlld  (gentle, confident)
#   "Elli"    — MF3mGyEYCl7XYWbV9V6O  (calm, empathetic)
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel


def get_voices(api_key: str) -> list:
    """List available voices on the account."""
    r = requests.get(f"{ELEVENLABS_BASE}/voices",
                     headers={"xi-api-key": api_key}, timeout=15)
    r.raise_for_status()
    return r.json().get("voices", [])


def generate_audio(api_key: str, text: str, voice_id: str,
                   model: str = "eleven_multilingual_v2") -> bytes:
    """Call ElevenLabs TTS and return raw audio bytes (mp3)."""
    payload = {
        "text": text,
        "model_id": model,
        "voice_settings": {
            "stability": 0.65,
            "similarity_boost": 0.80,
            "style": 0.25,
            "use_speaker_boost": True,
        },
    }
    r = requests.post(
        f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json=payload,
        timeout=120,
    )
    if r.status_code != 200:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise RuntimeError(f"ElevenLabs error {r.status_code}: {detail}")
    return r.content


def merge_audio_video(video_path: str, audio_path: str, output_path: str,
                      video_volume: float = 0.0, narration_volume: float = 1.0) -> None:
    """
    Merge narration audio with the video using FFmpeg.
    Set video_volume > 0 to mix in a background music track from the video's own audio.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-filter_complex",
        (f"[0:a]volume={video_volume}[va];"
         f"[1:a]volume={narration_volume}[na];"
         "[va][na]amix=inputs=2:duration=longest[aout]"),
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # If video has no audio track, fall back to simple mux
        cmd2 = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path,
        ]
        result2 = subprocess.run(cmd2, capture_output=True, text=True)
        if result2.returncode != 0:
            raise RuntimeError(f"FFmpeg merge failed:\n{result2.stderr}")


def main():
    parser = argparse.ArgumentParser(description="Dr. P ElevenLabs audio generator")
    parser.add_argument("--api-key", default=None,
                        help="ElevenLabs API key (or set ELEVENLABS_API_KEY env var)")
    parser.add_argument("--voice-id", default=DEFAULT_VOICE_ID,
                        help=f"ElevenLabs voice ID (default: Rachel {DEFAULT_VOICE_ID})")
    parser.add_argument("--list-voices", action="store_true",
                        help="List available voices and exit")
    parser.add_argument("--video", default=None,
                        help="Input video to add audio to (e.g. drp_wavespeed.mp4)")
    parser.add_argument("--output", default=None,
                        help="Output path (.mp4 if --video given, else .mp3)")
    parser.add_argument("--audio-only", action="store_true",
                        help="Only generate the narration MP3, do not merge with video")
    parser.add_argument("--script", default=None,
                        help="Path to a .txt file with custom narration script")
    parser.add_argument("--model", default="eleven_multilingual_v2",
                        help="ElevenLabs model ID")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        sys.exit("Error: provide --api-key or set ELEVENLABS_API_KEY env var")

    if args.list_voices:
        voices = get_voices(api_key)
        print(f"{'Name':<30} {'ID':<32} Category")
        print("-" * 80)
        for v in voices:
            print(f"{v['name']:<30} {v['voice_id']:<32} {v.get('category','')}")
        return

    script_text = FULL_SCRIPT
    if args.script:
        with open(args.script) as f:
            script_text = f.read()

    # Generate audio
    print(f"Generating narration with voice {args.voice_id}…")
    audio_bytes = generate_audio(api_key, script_text, args.voice_id, args.model)

    if args.audio_only or not args.video:
        out = args.output or "narration.mp3"
        with open(out, "wb") as f:
            f.write(audio_bytes)
        size_kb = len(audio_bytes) / 1024
        print(f"✓ Saved narration → {out}  ({size_kb:.0f} KB)")
        return

    # Merge with video
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_audio:
        tmp_audio.write(audio_bytes)
        tmp_path = tmp_audio.name

    video_path = args.video
    out = args.output or str(Path(video_path).stem) + "_with_audio.mp4"
    print(f"Merging audio + video → {out}…")
    try:
        merge_audio_video(video_path, tmp_path, out)
        size_mb = os.path.getsize(out) / 1024 / 1024
        print(f"✓ Done! {out}  ({size_mb:.1f} MB)")
        print("\nNext steps:")
        print(f"  • Add background music:  ffmpeg -i {out} -i bg_music.mp3 -filter_complex '[0:a][1:a]amix=inputs=2:weights=1 0.2' -c:v copy final.mp4")
        print(f"  • Add captions:          ffmpeg -i {out} -vf subtitles=captions.srt final_captioned.mp4")
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    main()
