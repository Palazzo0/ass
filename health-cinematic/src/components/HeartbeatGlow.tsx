import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PHASE_1_END, PHASE_2_END, PHASE_3_END, getPhaseProgress } from "../utils/phases";

// 72 bpm at 30fps = 36 frames per beat
const BEAT_FRAMES = 36;

const pulse = (frame: number): number => {
  const phase = (frame % BEAT_FRAMES) / BEAT_FRAMES;
  // lub (0.0 → 0.5) and dub (0.5 → 1.0)
  const lub = phase < 0.5 ? phase * 2 : 0;
  const dub = phase >= 0.5 ? (phase - 0.5) * 2 : 0;

  const lubP = interpolate(lub, [0, 0.10, 1], [0, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const dubP = interpolate(dub, [0, 0.10, 1], [0, 0.6, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return Math.max(lubP, dubP);
};

export const HeartbeatGlow: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const beat = pulse(frame);

  // Phase 1: barely present
  const p1 = getPhaseProgress(frame, durationInFrames, 0, PHASE_1_END);
  // Phase 2: strong, alarming glow
  const p2 = getPhaseProgress(frame, durationInFrames, 0.38, PHASE_2_END);
  // Phase 3: fades to stillness
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, PHASE_3_END);

  const intensity = interpolate(
    p2,
    [0, 0.3, 0.8, 1],
    [0.10, 0.30, 0.48, 0.42],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const endFade = interpolate(p3, [0, 0.6, 1], [1, 0.45, 0.15], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const p1Ramp  = interpolate(p1, [0, 1], [0, 0.10], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const glowOpacity  = beat * (p1Ramp + intensity) * endFade;
  const rimOpacity   = beat * intensity * 0.55 * endFade;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Central chest glow */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse 70% 50% at 50% 60%, rgba(240,60,20,1) 0%, rgba(200,30,10,0.65) 38%, transparent 72%)",
          opacity: glowOpacity,
        }}
      />
      {/* Outer rim pulse */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at 50% 50%, transparent 45%, rgba(140,10,10,0.7) 100%)",
          opacity: rimOpacity,
        }}
      />
    </AbsoluteFill>
  );
};
