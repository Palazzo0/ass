import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { seededRange } from "../utils/noise";

// Blood cells travel along simplified vessel paths
// Each cell has a progress value 0-1 representing how far along its path it is
// We use simple linear interpolation between control points

interface CellPath {
  points: [number, number][];  // [x%, y%] control points
}

const CELL_PATHS: CellPath[] = [
  // Right side descending
  { points: [[88, 0], [87, 15], [89, 30], [88, 45], [87, 60], [86, 75], [87, 95]] },
  // Right branch going left
  { points: [[87, 18], [82, 21], [76, 24], [70, 27], [65, 29]] },
  // Right branch lower
  { points: [[85, 37], [79, 40], [73, 44], [68, 48]] },
  // Left side descending
  { points: [[11, 0], [13, 15], [11, 30], [12, 45], [13, 60], [14, 75], [13, 95]] },
  // Left branch going right
  { points: [[13, 16], [19, 20], [25, 23], [33, 26], [40, 28]] },
  // Left branch lower
  { points: [[15, 34], [21, 38], [28, 42], [36, 47]] },
  // Bottom
  { points: [[18, 88], [30, 89], [50, 90], [70, 89], [83, 88]] },
];

const CELL_COUNT = 22;

interface Cell {
  pathIdx: number;
  speed: number;   // frames to traverse full path
  phase: number;   // start offset 0–1
  size: number;
  opacity: number;
}

const CELLS: Cell[] = Array.from({ length: CELL_COUNT }, (_, i) => ({
  pathIdx: Math.floor(seededRange(i * 9 + 1, 0, CELL_PATHS.length)),
  speed: seededRange(i * 9 + 2, 120, 300),
  phase: seededRange(i * 9 + 3, 0, 1),
  size: seededRange(i * 9 + 4, 4, 8),
  opacity: seededRange(i * 9 + 5, 0.2, 0.45),
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

  const globalOpacity = interpolate(
    frame,
    [0, 40, durationInFrames],
    [0, 1, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {CELLS.map((cell, i) => {
        const path = CELL_PATHS[cell.pathIdx % CELL_PATHS.length];
        const t = ((frame / cell.speed + cell.phase) % 1);
        const [x, y] = lerpPath(path.points, t);

        // Cells become slightly more visible at end (blood trying to push through)
        const endIntensity = interpolate(
          frame,
          [durationInFrames * 0.6, durationInFrames],
          [1, 1.4],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );

        const opacity = cell.opacity * globalOpacity * endIntensity;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              width: cell.size,
              height: cell.size * 0.7,
              borderRadius: "50%",
              background:
                "radial-gradient(circle at 40% 35%, rgba(220,80,80,0.95), rgba(160,30,30,0.8))",
              filter: "blur(0.6px)",
              opacity,
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
