import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { seededRange } from "../utils/noise";
import { PHASE_2_END, PHASE_3_END, getPhaseProgress } from "../utils/phases";

const CELL_PATHS = [
  { points: [[88, 2], [87, 15], [89, 30], [88, 45], [87, 60], [86, 75], [87, 94]] as [number, number][] },
  { points: [[87, 18], [82, 21], [76, 24], [70, 27], [65, 29]] as [number, number][] },
  { points: [[85, 37], [79, 40], [73, 44], [68, 48]] as [number, number][] },
  { points: [[11, 2], [13, 15], [11, 30], [12, 45], [13, 60], [14, 75], [13, 94]] as [number, number][] },
  { points: [[13, 16], [19, 20], [25, 23], [33, 26], [40, 28]] as [number, number][] },
  { points: [[15, 34], [21, 38], [28, 42], [36, 47]] as [number, number][] },
  { points: [[18, 88], [30, 89], [50, 90], [70, 89], [83, 88]] as [number, number][] },
];

const CELL_COUNT = 26;

const CELLS = Array.from({ length: CELL_COUNT }, (_, i) => ({
  pathIdx: Math.floor(seededRange(i * 9 + 1, 0, CELL_PATHS.length)),
  speed:   seededRange(i * 9 + 2, 90, 240),
  phase:   seededRange(i * 9 + 3, 0, 1),
  size:    seededRange(i * 9 + 4, 6, 11),
  opacity: seededRange(i * 9 + 5, 0.30, 0.58),
}));

const lerpPath = (points: [number, number][], t: number): [number, number] => {
  if (t <= 0) return points[0];
  if (t >= 1) return points[points.length - 1];
  const seg = t * (points.length - 1);
  const idx = Math.floor(seg);
  const frac = seg - idx;
  const a = points[Math.min(idx, points.length - 1)];
  const b = points[Math.min(idx + 1, points.length - 1)];
  return [a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac];
};

export const BloodCells: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const globalFade = interpolate(frame, [0, 45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Phase 2: cells glow brighter (blood under stress)
  const p2 = getPhaseProgress(frame, durationInFrames, 0.38, PHASE_2_END);
  const phase2Boost = interpolate(p2, [0, 1], [1, 1.6], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Phase 3: cells slow and fade (blocked flow)
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, PHASE_3_END);
  const phase3Speed  = interpolate(p3, [0, 1], [1, 0.35], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const phase3Fade   = interpolate(p3, [0, 1], [1, 0.4],  { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {CELLS.map((cell, i) => {
        const path = CELL_PATHS[cell.pathIdx % CELL_PATHS.length];
        const effectiveSpeed = cell.speed / phase3Speed;
        const t = ((frame / effectiveSpeed + cell.phase) % 1);
        const [x, y] = lerpPath(path.points, t);
        const opacity = cell.opacity * globalFade * phase2Boost * phase3Fade;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              width: cell.size,
              height: cell.size * 0.68,
              borderRadius: "50%",
              background:
                "radial-gradient(circle at 38% 32%, rgba(235,90,80,1), rgba(170,25,25,0.85))",
              filter: "blur(0.8px)",
              opacity,
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
