import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { seededRange } from "../utils/noise";

const MOTE_COUNT = 28;

interface Mote {
  x: number;
  y: number;
  size: number;
  speedY: number;
  speedX: number;
  opacity: number;
  phase: number;
  hue: number;
}

const MOTES: Mote[] = Array.from({ length: MOTE_COUNT }, (_, i) => ({
  x: seededRange(i * 11 + 1, 5, 95),
  y: seededRange(i * 11 + 2, 10, 90),
  size: seededRange(i * 11 + 3, 1.5, 4.5),
  speedY: seededRange(i * 11 + 4, -0.006, -0.002),   // slow upward % per frame
  speedX: seededRange(i * 11 + 5, -0.003, 0.003),
  opacity: seededRange(i * 11 + 6, 0.25, 0.55),
  phase: seededRange(i * 11 + 7, 0, 600),
  hue: seededRange(i * 11 + 8, 0, 1),
}));

export const DustMotes: React.FC = () => {
  const frame = useCurrentFrame();
  useVideoConfig();

  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {MOTES.map((mote, i) => {
        const t = (frame + mote.phase * 600) % 900;
        const y = mote.y + mote.speedY * t;
        const x = mote.x + mote.speedX * t + Math.sin(t * 0.01 + mote.phase * 6) * 1.5;

        // Warm golden tones: amber → warm white
        const warmth = mote.hue;
        const r = Math.round(255);
        const g = Math.round(180 + warmth * 50);
        const b = Math.round(80 + warmth * 80);

        // Subtle twinkle
        const twinkle = 0.7 + 0.3 * Math.sin(frame * 0.08 + mote.phase * 10);
        const opacity = mote.opacity * twinkle;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              width: mote.size,
              height: mote.size,
              borderRadius: "50%",
              background: `rgba(${r},${g},${b},1)`,
              filter: `blur(${mote.size * 0.4}px)`,
              opacity,
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
