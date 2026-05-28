import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { seededRange } from "../utils/noise";
import { PHASE_1_END, PHASE_2_END, PHASE_3_END, getPhaseProgress } from "../utils/phases";

const COUNT = 22;
const FLIGHT_FRAMES = 80;

const PARTICLES = Array.from({ length: COUNT }, (_, i) => ({
  x: seededRange(i * 13 + 1, 4, 96),
  y: seededRange(i * 13 + 2, 8, 92),
  offsetX: seededRange(i * 13 + 10, -15, 15),
  offsetY: seededRange(i * 13 + 11, -12, 12),
  baseSize: seededRange(i * 13 + 3, 5, 11),
  phase: seededRange(i * 13 + 7, 0, 1),
  hue: seededRange(i * 13 + 8, 0, 1),
  blur: seededRange(i * 13 + 9, 1, 3.5),
  floatX: seededRange(i * 13 + 4, -0.003, 0.003),
  floatY: seededRange(i * 13 + 5, -0.004, -0.001),
  floatPhase: seededRange(i * 13 + 6, 0, 600),
}));

export const CholesterolParticles: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const p1 = getPhaseProgress(frame, durationInFrames, 0, PHASE_1_END);
  const p2 = getPhaseProgress(frame, durationInFrames, PHASE_1_END, PHASE_2_END);
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, PHASE_3_END);

  const phase1Opacity = interpolate(p1, [0.3, 1], [0, 0.35], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const phase2Strength = interpolate(p2, [0, 0.25, 1], [0, 0.8, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const phase3Fade = interpolate(p3, [0, 0.5, 1], [1, 0.5, 0.1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {PARTICLES.map((p, i) => {
        const t = frame + p.floatPhase * 600;

        // Phase 1: gentle ambient float
        const floatX = p.x + p.floatX * t + Math.sin(t * 0.009 + p.floatPhase * 5) * 2.5;
        const floatY = p.y + p.floatY * t + Math.cos(t * 0.007 + p.floatPhase * 4) * 1.8;

        // Phase 2: fly toward camera (grow + move toward center)
        const flightT = (frame + p.phase * FLIGHT_FRAMES) % FLIGHT_FRAMES;
        const flightProg = flightT / FLIGHT_FRAMES;
        const ease = flightProg * flightProg;

        const spawnX = p.x + p.offsetX;
        const spawnY = p.y + p.offsetY;
        const flyX = spawnX + (50 - spawnX) * ease;
        const flyY = spawnY + (50 - spawnY) * ease;

        const x = floatX + (flyX - floatX) * phase2Strength;
        const y = floatY + (flyY - floatY) * phase2Strength;

        const flyScale = 1 + flightProg * 5.5 * phase2Strength;
        const size = p.baseSize * flyScale;

        const flightOpacity = flightProg < 0.15
          ? flightProg / 0.15
          : flightProg > 0.72
            ? (1 - flightProg) / 0.28
            : 1;

        const globalOpacity =
          (phase1Opacity * (1 - phase2Strength) + flightOpacity * phase2Strength)
          * phase3Fade;

        const twinkle = 0.75 + 0.25 * Math.sin(frame * 0.06 + p.floatPhase * 9);
        const opacity = globalOpacity * twinkle;

        const g = Math.round(185 + p.hue * 42);
        const b = Math.round(18 + p.hue * 32);

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              width: size,
              height: size * 0.78,
              borderRadius: "50%",
              background: `radial-gradient(circle at 38% 32%, rgba(255,${g},${b},0.96), rgba(195,135,18,0.55))`,
              filter: `blur(${p.blur * (1 + flightProg * 1.5 * phase2Strength)}px)`,
              opacity,
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
