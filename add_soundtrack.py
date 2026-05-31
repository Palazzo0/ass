"""
Dr. P's Corner — Cinematic Soundtrack Mixer
Synthesizes the sound design layers described in the brief and merges
them with the trailer video using FFmpeg.

Layers:
  - Deep cinematic trailer bass drone
  - Subtle heartbeat ambience
  - Blood-flow whoosh transitions
  - Low atmospheric riser before smoking reveal
  - Subtle ringing effect before smoking reveal
  - Final emotional ambient fade

Usage:
    python add_soundtrack.py --video drp_trailer.mp4 --output drp_final.mp4
    python add_soundtrack.py --video drp_trailer.mp4 --narration narration.mp3 --output drp_final.mp4
"""

import argparse
import os
import struct
import subprocess
import sys
import wave
from pathlib import Path

# ─── PURE-PYTHON WAV SYNTHESIZER ─────────────────────────────────────────────
# Generates cinematic sound layers without any external audio libraries.

import math
import array as _array

SAMPLE_RATE = 44100


def sine(freq: float, duration: float, amp: float = 0.5) -> list:
    n = int(duration * SAMPLE_RATE)
    return [amp * math.sin(2 * math.pi * freq * i / SAMPLE_RATE) for i in range(n)]


def noise(duration: float, amp: float = 0.05) -> list:
    import random
    n = int(duration * SAMPLE_RATE)
    return [amp * (random.random() * 2 - 1) for _ in range(n)]


def envelope(samples: list, attack: float = 0.1, release: float = 0.3) -> list:
    n = len(samples)
    a_n = int(attack * SAMPLE_RATE)
    r_n = int(release * SAMPLE_RATE)
    out = list(samples)
    for i in range(min(a_n, n)):
        out[i] *= i / a_n
    for i in range(min(r_n, n)):
        idx = n - 1 - i
        out[idx] *= i / r_n
    return out


def mix(*tracks) -> list:
    max_len = max(len(t) for t in tracks)
    result = [0.0] * max_len
    for track in tracks:
        for i, s in enumerate(track):
            result[i] += s
    return result


def pad(samples: list, total_dur: float) -> list:
    n = int(total_dur * SAMPLE_RATE)
    if len(samples) >= n:
        return samples[:n]
    return samples + [0.0] * (n - len(samples))


def write_wav(path: str, samples: list, sr: int = SAMPLE_RATE):
    peak = max(abs(s) for s in samples) if samples else 1.0
    if peak > 0.9:
        samples = [s * 0.9 / peak for s in samples]
    int_samples = [max(-32768, min(32767, int(s * 32767))) for s in samples]
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        raw = _array.array("h", int_samples)
        wf.writeframes(raw.tobytes())


def generate_soundtrack(total_dur: float, output_path: str):
    """Synthesise all cinematic sound layers and write a mono WAV."""
    print("  Synthesising cinematic soundtrack…")

    # ── 1. Deep bass drone (sub 40–60Hz) ─────────────────────────────────
    bass = sine(42, total_dur, amp=0.30)
    bass2 = sine(55, total_dur, amp=0.18)
    bass = mix(bass, bass2)
    # LFO modulation on bass
    lfo_rate = 0.08
    bass = [bass[i] * (0.7 + 0.3 * math.sin(2 * math.pi * lfo_rate * i / SAMPLE_RATE))
            for i in range(len(bass))]

    # ── 2. Heartbeat (70bpm ≈ every 0.857s) ──────────────────────────────
    hb_interval = 0.857
    hb = [0.0] * int(total_dur * SAMPLE_RATE)
    for beat_t in [i * hb_interval for i in range(int(total_dur / hb_interval) + 1)]:
        # Double thump: lub-dub
        for offset, freq, amp in [(0, 80, 0.55), (0.12, 65, 0.35)]:
            start = int((beat_t + offset) * SAMPLE_RATE)
            dur_s = 0.09
            for j in range(int(dur_s * SAMPLE_RATE)):
                idx = start + j
                if idx < len(hb):
                    env = math.sin(math.pi * j / (dur_s * SAMPLE_RATE))
                    hb[idx] += amp * env * math.sin(2 * math.pi * freq * j / SAMPLE_RATE)

    # Accelerate heartbeat toward smoking reveal (scene 7 ≈ 30s)
    hb_mod = []
    for i, s in enumerate(hb):
        t = i / SAMPLE_RATE
        tension = clamp_val((t - 25) / 8, 0, 1)  # ramps up 25–33s
        hb_mod.append(s * (1.0 + 0.4 * tension))
    hb = hb_mod

    # ── 3. Atmospheric pad (soft strings texture) ─────────────────────────
    pad_freqs = [110, 138.6, 164.8, 220]
    atm = [0.0] * int(total_dur * SAMPLE_RATE)
    for freq in pad_freqs:
        layer = sine(freq, total_dur, amp=0.08)
        layer = [layer[i] * (0.5 + 0.5 * math.sin(2 * math.pi * 0.05 * i / SAMPLE_RATE))
                 for i in range(len(layer))]
        for i in range(len(atm)):
            atm[i] += layer[i]

    # ── 4. Whoosh transitions at scene cuts ───────────────────────────────
    cut_times = [3.5, 8.5, 12.0, 14.5, 19.0, 23.5, 27.0, 30.5, 33.5]
    whoosh_track = [0.0] * int(total_dur * SAMPLE_RATE)
    for ct in cut_times:
        dur_w = 0.4
        n_w = int(dur_w * SAMPLE_RATE)
        start = int(ct * SAMPLE_RATE)
        # Descending white-noise whoosh
        for j in range(n_w):
            idx = start + j
            if idx < len(whoosh_track):
                env = math.sin(math.pi * j / n_w) ** 2
                freq_w = 800 - 600 * (j / n_w)
                whoosh_track[idx] += 0.25 * env * math.sin(2 * math.pi * freq_w * j / SAMPLE_RATE)

    # ── 5. Bass hit when plaque/impact moments ────────────────────────────
    impact_times = [8.8, 12.2, 19.2, 23.6, 30.6]
    impacts = [0.0] * int(total_dur * SAMPLE_RATE)
    for it in impact_times:
        dur_i = 0.15
        n_i = int(dur_i * SAMPLE_RATE)
        start = int(it * SAMPLE_RATE)
        for j in range(n_i):
            idx = start + j
            if idx < len(impacts):
                env = (1 - j / n_i) ** 2
                impacts[idx] += 0.65 * env * math.sin(2 * math.pi * 50 * j / SAMPLE_RATE)

    # ── 6. Ringing before smoking reveal (≈ 29s) ─────────────────────────
    ring_start = int(29.2 * SAMPLE_RATE)
    ring_dur = 1.2
    ring_n = int(ring_dur * SAMPLE_RATE)
    ring = [0.0] * int(total_dur * SAMPLE_RATE)
    for j in range(ring_n):
        idx = ring_start + j
        if idx < len(ring):
            env = math.sin(math.pi * j / ring_n) * math.exp(-3 * j / ring_n)
            ring[idx] = 0.3 * env * math.sin(2 * math.pi * 880 * j / SAMPLE_RATE)

    # ── 7. Cinematic riser (25→30s) ───────────────────────────────────────
    riser = [0.0] * int(total_dur * SAMPLE_RATE)
    riser_start = int(25.0 * SAMPLE_RATE)
    riser_dur = 5.0
    riser_n = int(riser_dur * SAMPLE_RATE)
    for j in range(riser_n):
        idx = riser_start + j
        if idx < len(riser):
            frac = j / riser_n
            freq_r = 100 + 900 * frac ** 2
            env = frac ** 0.5
            riser[idx] = 0.18 * env * math.sin(2 * math.pi * freq_r * j / SAMPLE_RATE)

    # ── 8. Final fade-out ambience ────────────────────────────────────────
    fade_start = total_dur - 4.0
    final_amp = []
    for i in range(int(total_dur * SAMPLE_RATE)):
        t = i / SAMPLE_RATE
        if t < fade_start:
            final_amp.append(1.0)
        else:
            final_amp.append(max(0, 1 - (t - fade_start) / 4.0))

    # ── Mix all layers ────────────────────────────────────────────────────
    soundtrack = mix(bass, hb, atm, whoosh_track, impacts, ring, riser)
    soundtrack = [soundtrack[i] * final_amp[i] for i in range(len(soundtrack))]

    write_wav(output_path, soundtrack)
    print(f"  Soundtrack written → {output_path}")


def clamp_val(v, lo, hi):
    return max(lo, min(hi, v))


def merge(video_path: str, soundtrack_path: str, narration_path: str,
          output_path: str):
    """Merge video + generated soundtrack + optional narration using FFmpeg."""
    inputs = ["-i", video_path, "-i", soundtrack_path]
    if narration_path and os.path.exists(narration_path):
        inputs += ["-i", narration_path]
        # narration loud, soundtrack quiet underneath
        filter_complex = (
            "[1:a]volume=0.35[st];"
            "[2:a]volume=1.0[nar];"
            "[st][nar]amix=inputs=2:duration=longest[aout]"
        )
        map_args = ["-map", "0:v", "-map", "[aout]"]
    else:
        filter_complex = "[1:a]volume=0.5[aout]"
        map_args = ["-map", "0:v", "-map", "[aout]"]

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + ["-filter_complex", filter_complex]
        + map_args
        + ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", output_path]
    )
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg error:", result.stderr[-800:])
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Dr. P Cinematic Soundtrack Mixer")
    parser.add_argument("--video", required=True, help="Input trailer video")
    parser.add_argument("--narration", default=None, help="Optional narration MP3")
    parser.add_argument("--output", default="drp_final.mp4")
    parser.add_argument("--soundtrack-only", action="store_true",
                        help="Only generate the WAV, do not merge")
    args = parser.parse_args()

    # Get video duration via ffprobe
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", args.video],
        capture_output=True, text=True
    )
    total_dur = float(result.stdout.strip()) if result.returncode == 0 else 41.0
    print(f"Video duration: {total_dur:.1f}s")

    wav_path = args.output.replace(".mp4", "_soundtrack.wav")
    generate_soundtrack(total_dur, wav_path)

    if args.soundtrack_only:
        print(f"Done — {wav_path}")
        return

    print(f"Merging → {args.output}…")
    merge(args.video, wav_path, args.narration, args.output)
    size_mb = os.path.getsize(args.output) / 1024 / 1024
    print(f"✓ {args.output}  ({size_mb:.1f} MB)")
    os.unlink(wav_path)


if __name__ == "__main__":
    main()
