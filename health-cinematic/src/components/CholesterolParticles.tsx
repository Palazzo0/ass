import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { seededRange } from "../utils/noise";
import { PHASE_1_END, PHASE_2_END, getPhaseProgress } from "../utils/phases";

const COUNT = 18;

const PARTICLES = Array.from({ length: COUNT }, (_, i) => ({
  x:       seededRange(i * 13 + 1, 8, 92),
  y:       seededRange(i * 13 + 2, 15, 85),
  size:    seededRange(i * 13 + 3, 6, 14),
  speedX:  seededRange(i * 13 + 4, -0.004, 0.004),
  speedY:  seededRange(i * 13 + 5, -0.003, 0.003),
  opacity: seededRange(i * 13 + 6, 0.30, 0.55),
  phase:   seededRange(i * 13 + 7, 0, 500),
  blur:    seededRange(i * 13 + 8, 1.5, 4),
  hue:     seededRange(i * 13 + 9, 0, 1), // 0=yellow, 1=gold-orange
}));

export const CholesterolParticles: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Appear in phase 2, fade in phase 3
  const p2 = getPhaseProgress(frame, durationInFrames, PHASE_1_END, PHASE_2_END);
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, 1.0);
  const globalOpacity =
    interpolate(p2, [0, 0.3, 1], [0, 0.7, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) *
    interpolate(p3, [0, 0.7, 1], [1, 0.6, 0.2], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {PARTICLES.map((p, i) => {
        const t = frame + p.phase * 500;
        const x = p.x + p.speedX * t + Math.sin(t * 0.008 + p.phase * 4) * 3;
        const y = p.y + p.speedY * t + Math.cos(t * 0.007 + p.phase * 3) * 2;

        const g = Math.round(190 + p.hue * 40); // 190–230
        const b = Math.round(20 + p.hue * 30);  //  20–50
        const twinkle = 0.7 + 0.3 * Math.sin(frame * 0.07 + p.phase * 8);
        const opacity = p.opacity * twinkle * globalOpacity;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              width: p.size,
              height: p.size * 0.8,
              borderRadius: "50%",
              background: `radial-gradient(circle at 40% 35%, rgba(255,${g},${b},0.95), rgba(200,140,20,0.5))`,
              filter: `blur(${p.blur}px)`,
              opacity,
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
