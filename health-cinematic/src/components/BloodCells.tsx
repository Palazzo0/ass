import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { seededRange } from "../utils/noise";
import { PHASE_2_END, PHASE_3_END, getPhaseProgress } from "../utils/phases";

// Vessel paths as percentage coordinates
const PATHS = [
  { pts: [[91, 1], [90, 15], [91, 30], [90, 45], [89, 60], [88, 75], [89, 96]] as [number, number][] },
  { pts: [[90, 22], [84, 25], [77, 27], [70, 29], [63, 30]] as [number, number][] },
  { pts: [[88, 42], [81, 46], [74, 50], [67, 54]] as [number, number][] },
  { pts: [[9, 1], [11, 15], [9, 30], [10, 45], [11, 60], [12, 75], [11, 96]] as [number, number][] },
  { pts: [[10, 20], [17, 23], [24, 26], [32, 28], [40, 30]] as [number, number][] },
  { pts: [[12, 40], [19, 44], [27, 48], [35, 52]] as [number, number][] },
  { pts: [[17, 88], [30, 89], [52, 90], [72, 89], [85, 88]] as [number, number][] },
];

const CELL_COUNT = 30;

const CELLS = Array.from({ length: CELL_COUNT }, (_, i) => ({
  pathIdx: Math.floor(seededRange(i * 9 + 1, 0, PATHS.length)),
  speed:   seededRange(i * 9 + 2, 80, 210),
  phase:   seededRange(i * 9 + 3, 0, 1),
  size:    seededRange(i * 9 + 4, 6, 12),
  opacity: seededRange(i * 9 + 5, 0.28, 0.55),
}));

const lerpPath = (pts: [number, number][], t: number): [number, number] => {
  if (t <= 0) return pts[0];
  if (t >= 1) return pts[pts.length - 1];
  const seg = t * (pts.length - 1);
  const idx = Math.floor(seg);
  const frac = seg - idx;
  const a = pts[Math.min(idx, pts.length - 1)];
  const b = pts[Math.min(idx + 1, pts.length - 1)];
  return [a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac];
};

export const BloodCells: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const globalFade = interpolate(frame, [0, 50], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Phase 2: cells energized / brighter (stress response)
  const p2 = getPhaseProgress(frame, durationInFrames, 0.38, PHASE_2_END);
  const phase2Boost = interpolate(p2, [0, 1], [1, 1.7], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Pre-flash blood RUSH: cells surge faster and grow just before the impact
  const flashFrame = Math.round(durationInFrames * 0.645);
  const rushSpeed = interpolate(
    frame,
    [flashFrame - 35, flashFrame - 10, flashFrame, flashFrame + 5],
    [1, 3.8, 2.2, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  // Cells grow larger during rush (flying toward camera feel)
  const rushScale = interpolate(
    frame,
    [flashFrame - 35, flashFrame - 10, flashFrame, flashFrame + 5],
    [1, 2.2, 1.5, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Phase 3: cells slow to a crawl, fade away (blocked flow)
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, PHASE_3_END);
  const phase3SpeedFactor = interpolate(p3, [0, 0.5, 1], [1, 0.4, 0.18], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const phase3Fade        = interpolate(p3, [0, 0.4, 1], [1, 0.55, 0.18], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {CELLS.map((cell, i) => {
        const path = PATHS[cell.pathIdx % PATHS.length];
        const effectiveSpeed = cell.speed / (phase3SpeedFactor * rushSpeed);
        const t = (frame / effectiveSpeed + cell.phase) % 1;
        const [x, y] = lerpPath(path.pts, t);
        const opacity = cell.opacity * globalFade * phase2Boost * phase3Fade;
        const scaledSize = cell.size * rushScale;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              width: scaledSize,
              height: scaledSize * 0.68,
              borderRadius: "50%",
              background:
                "radial-gradient(circle at 38% 32%, rgba(238,85,72,1), rgba(168,22,22,0.88))",
              filter: "blur(0.9px)",
              opacity,
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
