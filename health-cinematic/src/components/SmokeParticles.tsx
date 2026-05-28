import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { seededRange } from "../utils/noise";

const SMOKE_COUNT = 9;

interface SmokeBlob {
  startX: number;   // % of width
  startY: number;   // % of height (start position — bottom half)
  size: number;     // px radius
  speed: number;    // frames per full-height drift
  driftX: number;   // horizontal drift amplitude in %
  opacity: number;  // max opacity
  phase: number;    // frame offset
  blur: number;     // blur amount px
}

const BLOBS: SmokeBlob[] = Array.from({ length: SMOKE_COUNT }, (_, i) => ({
  startX: seededRange(i * 7 + 1, 5, 95),
  startY: seededRange(i * 7 + 2, 55, 105),
  size: seededRange(i * 7 + 3, 120, 260),
  speed: seededRange(i * 7 + 4, 400, 800),
  driftX: seededRange(i * 7 + 5, -6, 6),
  opacity: seededRange(i * 7 + 6, 0.03, 0.07),
  phase: seededRange(i * 7 + 7, 0, 300),
  blur: seededRange(i * 7 + 8, 40, 80),
}));

export const SmokeParticles: React.FC = () => {
  const frame = useCurrentFrame();
  useVideoConfig();

  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {BLOBS.map((blob, i) => {
        const t = ((frame + blob.phase) % blob.speed) / blob.speed;
        // Drift upward from startY toward 0 (top)
        const y = blob.startY - t * 120;
        // Gentle horizontal oscillation
        const x = blob.startX + Math.sin(t * Math.PI * 2) * blob.driftX;
        // Fade in from bottom, fade out near top
        const fadeIn = Math.min(1, t * 5);
        const fadeOut = Math.min(1, (1 - t) * 4);
        const opacity = blob.opacity * fadeIn * fadeOut;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              width: blob.size,
              height: blob.size,
              borderRadius: "50%",
              background:
                "radial-gradient(circle, rgba(210,190,170,0.9) 0%, rgba(180,160,140,0.4) 50%, transparent 100%)",
              filter: `blur(${blob.blur}px)`,
              opacity,
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
