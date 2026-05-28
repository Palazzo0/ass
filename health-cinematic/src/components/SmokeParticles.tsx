import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { seededRange } from "../utils/noise";
import { getPhaseProgress, PHASE_2_END } from "../utils/phases";

const SMOKE_COUNT = 10;

const BLOBS = Array.from({ length: SMOKE_COUNT }, (_, i) => ({
  startX: seededRange(i * 7 + 1, 3, 97),
  startY: seededRange(i * 7 + 2, 60, 110),
  size:   seededRange(i * 7 + 3, 160, 320),
  speed:  seededRange(i * 7 + 4, 350, 700),
  driftX: seededRange(i * 7 + 5, -8, 8),
  opacity: seededRange(i * 7 + 6, 0.07, 0.16),
  phase:  seededRange(i * 7 + 7, 0, 300),
  blur:   seededRange(i * 7 + 8, 50, 90),
}));

export const SmokeParticles: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const globalFade = interpolate(frame, [0, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Smoke intensifies slightly in phase 2, then lingers in phase 3
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, 1.0);
  const phaseMultiplier = 1 + interpolate(p3, [0, 1], [0, 0.3], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {BLOBS.map((blob, i) => {
        const t = ((frame + blob.phase) % blob.speed) / blob.speed;
        const y = blob.startY - t * 130;
        const x = blob.startX + Math.sin(t * Math.PI * 2) * blob.driftX;
        const fadeIn  = Math.min(1, t * 4);
        const fadeOut = Math.min(1, (1 - t) * 3);
        const opacity = blob.opacity * fadeIn * fadeOut * globalFade * phaseMultiplier;

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
                "radial-gradient(circle, rgba(200,180,160,0.85) 0%, rgba(160,140,120,0.35) 50%, transparent 100%)",
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
