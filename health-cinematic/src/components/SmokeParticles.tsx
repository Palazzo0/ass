import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { seededRange } from "../utils/noise";
import { PHASE_2_END, PHASE_3_END, getPhaseProgress } from "../utils/phases";

const COUNT = 12;

const BLOBS = Array.from({ length: COUNT }, (_, i) => ({
  x:       seededRange(i * 7 + 1, 5, 95),
  y:       seededRange(i * 7 + 2, 10, 90),
  size:    seededRange(i * 7 + 3, 220, 420),
  speedY:  seededRange(i * 7 + 4, -0.008, -0.002),
  speedX:  seededRange(i * 7 + 5, -0.003, 0.003),
  opacity: seededRange(i * 7 + 6, 0.07, 0.17),
  phase:   seededRange(i * 7 + 7, 0, 900),
  hue:     seededRange(i * 7 + 8, 0, 1),
}));

export const SmokeParticles: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const globalFade = interpolate(frame, [0, 45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, PHASE_3_END);
  const densityBoost = interpolate(p3, [0, 1], [1, 1.45], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {BLOBS.map((b, i) => {
        const t = (frame + b.phase) % 900;
        const y = b.y + b.speedY * t;
        const x = b.x + b.speedX * t + Math.sin(t * 0.008 + b.phase * 0.5) * 3;
        const pulse = 0.7 + 0.3 * Math.sin(frame * 0.015 + b.phase * 0.4);
        const r = Math.round(110 + b.hue * 35);
        const g = Math.round(95 + b.hue * 30);
        const bC = Math.round(85 + b.hue * 20);

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              width: b.size,
              height: b.size * 0.65,
              borderRadius: "50%",
              background: `rgba(${r},${g},${bC},0.55)`,
              filter: `blur(${b.size * 0.22}px)`,
              opacity: b.opacity * pulse * globalFade * densityBoost,
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
