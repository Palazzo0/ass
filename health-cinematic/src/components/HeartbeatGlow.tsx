import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PHASE_1_END, PHASE_2_END, PHASE_3_END, getPhaseProgress } from "../utils/phases";

const BEAT_FRAMES = 36;

function pulse(frame: number): number {
  const ph = (frame % BEAT_FRAMES) / BEAT_FRAMES;
  const lub = ph < 0.5 ? ph * 2 : 0;
  const dub = ph >= 0.5 ? (ph - 0.5) * 2 : 0;
  const lubP = interpolate(lub, [0, 0.09, 1], [0, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const dubP = interpolate(dub, [0, 0.09, 1], [0, 0.62, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return Math.max(lubP, dubP);
}

export const HeartbeatGlow: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const beat = pulse(frame);

  const p1 = getPhaseProgress(frame, durationInFrames, 0, PHASE_1_END);
  const p2 = getPhaseProgress(frame, durationInFrames, 0.38, PHASE_2_END);
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, PHASE_3_END);

  // p1: barely there
  const p1Ramp = interpolate(p1, [0, 1], [0, 0.10], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // p2: building alarm
  const intensity = interpolate(
    p2,
    [0, 0.25, 0.75, 1],
    [0.08, 0.32, 0.52, 0.46],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // p3: fades to stillness — slower fade for emotional weight
  const endFade = interpolate(p3, [0, 0.5, 0.9, 1], [1, 0.65, 0.22, 0.1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const glowOpacity = beat * (p1Ramp + intensity) * endFade;
  const rimOpacity  = beat * intensity * 0.65 * endFade;

  // Extra: steady ambient red wash in phase 2 (between beats)
  const ambientWash = interpolate(p2, [0, 0.3, 1], [0, 0.04, 0.07], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
    * interpolate(p3, [0, 0.5, 1], [1, 0.5, 0.1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Ambient inter-beat wash */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse 60% 42% at 50% 62%, rgba(200,30,10,0.7) 0%, transparent 75%)",
          opacity: ambientWash,
        }}
      />
      {/* Central chest glow */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse 72% 52% at 50% 60%, rgba(245,50,15,1) 0%, rgba(210,25,8,0.70) 35%, transparent 70%)",
          opacity: glowOpacity,
        }}
      />
      {/* Outer rim shock ring */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at 50% 50%, transparent 42%, rgba(150,8,8,0.75) 100%)",
          opacity: rimOpacity,
        }}
      />
    </AbsoluteFill>
  );
};
