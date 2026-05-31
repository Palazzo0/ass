#!/usr/bin/env node
// Generates cinematic audio WAV files for the health documentary overlay.
// Run: node generate-audio.js

const fs = require("fs");
const path = require("path");

const SAMPLE_RATE = 44100;

// ── WAV writer ─────────────────────────────────────────────────────────────
function writeWav(filePath, samples) {
  const dataBytes = samples.length * 2;
  const buf = Buffer.alloc(44 + dataBytes);

  buf.write("RIFF", 0);
  buf.writeUInt32LE(36 + dataBytes, 4);
  buf.write("WAVE", 8);
  buf.write("fmt ", 12);
  buf.writeUInt32LE(16, 16);        // chunk size
  buf.writeUInt16LE(1, 20);         // PCM
  buf.writeUInt16LE(1, 22);         // mono
  buf.writeUInt32LE(SAMPLE_RATE, 24);
  buf.writeUInt32LE(SAMPLE_RATE * 2, 28);
  buf.writeUInt16LE(2, 32);         // block align
  buf.writeUInt16LE(16, 34);        // bits per sample
  buf.write("data", 36);
  buf.writeUInt32LE(dataBytes, 40);

  for (let i = 0; i < samples.length; i++) {
    const v = Math.max(-1, Math.min(1, samples[i]));
    buf.writeInt16LE(Math.round(v * 32767), 44 + i * 2);
  }

  fs.writeFileSync(filePath, buf);
}

// ── Ambient cinematic drone (16 s) ─────────────────────────────────────────
// Deep resonant hum — layers at 38Hz, 48Hz, 76Hz with slow tremolo/beatings
function makeDrone(duration = 16) {
  const n = Math.ceil(duration * SAMPLE_RATE);
  const s = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const t = i / SAMPLE_RATE;
    const progress = t / duration;

    const base  = 0.18 * Math.sin(2 * Math.PI * 38 * t);
    const sub   = 0.12 * Math.sin(2 * Math.PI * 48 * t + 0.3);
    const oct   = 0.06 * Math.sin(2 * Math.PI * 76 * t);
    const high  = 0.02 * Math.sin(2 * Math.PI * 152 * t);

    // Very slow beating / AM modulation
    const beatMod = 1 + 0.12 * Math.sin(2 * Math.PI * 0.18 * t);

    // Envelope: fade in 2 s, sustain, fade out 2 s
    const env = Math.min(1, t / 2) * Math.min(1, (duration - t) / 2);

    // Build intensity toward phase 2 (~40-72% = t 6-10.8 s in 15 s video)
    const build = 1 + 0.35 * Math.max(0, Math.min(1, (t - 5) / 5));

    s[i] = (base + sub + oct + high) * beatMod * env * build;
  }
  return s;
}

// ── Heartbeat loop (4.8 s = 4 beats at ~50bpm matching BEAT_FRAMES=36@30fps)
// Lub-dub pattern: lub at 0%, dub at 50%
// One beat = 36/30 = 1.2 s → 4 beats = 4.8 s
function makeHeartbeatLoop() {
  const BEAT_S = 36 / 30;           // 1.2 s per beat (matches BEAT_FRAMES=36 at 30fps)
  const BEATS  = 4;
  const duration = BEAT_S * BEATS;  // 4.8 s
  const n = Math.ceil(duration * SAMPLE_RATE);
  const s = new Float32Array(n);

  for (let i = 0; i < n; i++) {
    const t = i / SAMPLE_RATE;
    const beatPhase = (t % BEAT_S) / BEAT_S;

    // Lub: 0-8% of beat — strong, low
    if (beatPhase < 0.08) {
      const p = beatPhase / 0.08;
      const env = Math.sin(p * Math.PI) ** 2;
      s[i] += env * (
        0.30 * Math.sin(2 * Math.PI * 62 * t) +
        0.18 * Math.sin(2 * Math.PI * 82 * t) +
        0.08 * Math.sin(2 * Math.PI * 110 * t)
      );
    }

    // Dub: 50-60% of beat — softer
    if (beatPhase >= 0.50 && beatPhase < 0.60) {
      const p = (beatPhase - 0.50) / 0.10;
      const env = Math.sin(p * Math.PI) ** 2;
      s[i] += env * (
        0.20 * Math.sin(2 * Math.PI * 58 * t) +
        0.12 * Math.sin(2 * Math.PI * 76 * t)
      );
    }
  }

  // Gentle fade in/out at loop edges to prevent clicks
  const fadeLen = Math.round(0.05 * SAMPLE_RATE);
  for (let i = 0; i < fadeLen; i++) {
    const f = i / fadeLen;
    s[i] *= f;
    s[n - 1 - i] *= f;
  }

  return s;
}

// ── Cinematic boom (2.5 s) — plays at "stroke or heart attack" moment ───────
function makeBoom(duration = 2.5) {
  const n = Math.ceil(duration * SAMPLE_RATE);
  const s = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const t = i / SAMPLE_RATE;
    // Fast attack, exponential decay
    const env = Math.exp(-t * 2.8);
    // Descending pitch for impact feel
    const freq = 45 * Math.exp(-t * 1.2);
    s[i] =
      env * 0.45 * Math.sin(2 * Math.PI * (42 + freq) * t) +
      env * 0.22 * Math.sin(2 * Math.PI * (85 + freq * 0.5) * t) +
      env * 0.10 * Math.sin(2 * Math.PI * 168 * t);
    // Sub-bass rumble
    s[i] += env * 0.15 * Math.sin(2 * Math.PI * 28 * t) * Math.exp(-t * 1.5);
  }
  return s;
}

// ── Tension riser (8 s) — phase 3 atmospheric buildup ──────────────────────
function makeRiser(duration = 8) {
  const n = Math.ceil(duration * SAMPLE_RATE);
  const s = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const t = i / SAMPLE_RATE;
    const prog = t / duration;

    // Rising frequency: 28Hz → 55Hz
    const freq = 28 + prog * 27;
    const env = prog * prog * 0.28; // accelerating build

    s[i] =
      env * Math.sin(2 * Math.PI * freq * t) +
      env * 0.45 * Math.sin(2 * Math.PI * freq * 2 * t) +
      env * 0.20 * Math.sin(2 * Math.PI * freq * 3 * t);

    // Add pink-ish noise flutter
    const noise = (Math.sin(i * 1.234) + Math.sin(i * 0.567) + Math.sin(i * 0.891)) / 3;
    s[i] += env * 0.08 * noise;
  }

  // Fade in 0.4 s, fade out last 1 s
  const fadeIn  = Math.round(0.4 * SAMPLE_RATE);
  const fadeOut = Math.round(1.0 * SAMPLE_RATE);
  for (let i = 0; i < fadeIn; i++) s[i] *= i / fadeIn;
  for (let i = 0; i < fadeOut; i++) s[n - 1 - i] *= i / fadeOut;

  return s;
}

// ── Write all files ─────────────────────────────────────────────────────────
const dir = path.join(__dirname, "public/sounds");
fs.mkdirSync(dir, { recursive: true });

console.log("Generating audio files…");

writeWav(path.join(dir, "drone.wav"), makeDrone(40));
console.log("  ✓ drone.wav (40 s ambient drone)");

writeWav(path.join(dir, "heartbeat-loop.wav"), makeHeartbeatLoop());
console.log("  ✓ heartbeat-loop.wav (4.8 s loop, 4 beats)");

writeWav(path.join(dir, "boom.wav"), makeBoom(2.5));
console.log("  ✓ boom.wav (2.5 s cinematic boom)");

writeWav(path.join(dir, "riser.wav"), makeRiser(8));
console.log("  ✓ riser.wav (8 s tension riser)");

console.log("Done.");
