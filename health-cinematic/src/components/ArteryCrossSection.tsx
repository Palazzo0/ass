import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PHASE_3_START, PHASE_4_START, getPhaseProgress } from "../utils/phases";

// Interior artery cross-section view — appears in Phase 3 to show plaque
// building on vessel walls and the lumen progressively narrowing.

const OUTER_R      = 130;
const INNER_WALL_R = 120; // inner surface of vessel wall where plaque attaches
const BASE_LUMEN_R = 110; // full, healthy lumen radius

type Deposit = { start: number; span: number; maxFrac: number; delay: number };

const DEPOSITS: Deposit[] = [
  { start: -45, span: 85,  maxFrac: 0.56, delay: 0.00 },
  { start: 95,  span: 60,  maxFrac: 0.48, delay: 0.08 },
  { start: 195, span: 72,  maxFrac: 0.54, delay: 0.05 },
  { start: 300, span: 48,  maxFrac: 0.38, delay: 0.14 },
];

function arcPath(
  cx: number, cy: number,
  r1: number, r2: number,
  startDeg: number, spanDeg: number
): string {
  const R = Math.PI / 180;
  const a1 = startDeg * R;
  const a2 = (startDeg + spanDeg) * R;
  const large = spanDeg > 180 ? 1 : 0;
  const p = (r: number, a: number) =>
    `${(cx + r * Math.cos(a)).toFixed(2)} ${(cy + r * Math.sin(a)).toFixed(2)}`;
  return `M ${p(r2, a1)} A ${r2} ${r2} 0 ${large} 1 ${p(r2, a2)} L ${p(r1, a2)} A ${r1} ${r1} 0 ${large} 0 ${p(r1, a1)} Z`;
}

export const ArteryCrossSection: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();

  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_3_START, 1.0);
  const p4 = getPhaseProgress(frame, durationInFrames, PHASE_4_START, 1.0);

  const overlayOpacity = interpolate(
    p3,
    [0, 0.10, 0.88, 1.0],
    [0, 0.44, 0.40, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  if (overlayOpacity < 0.005) return null;

  const cx = width / 2;
  const cy = height * 0.80;

  // Total plaque growth: Phase 3 contributes 0→65%, Phase 4 pushes 0→28% extra
  const plaqueProgress =
    interpolate(p3, [0, 1], [0, 0.65], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) +
    interpolate(p4, [0, 1], [0, 0.28], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Lumen shrinks from BASE_LUMEN_R toward ~32% of OUTER_R (critical stenosis)
  const minLumen = OUTER_R * 0.30;
  const lumenR   = BASE_LUMEN_R - (BASE_LUMEN_R - minLumen) * Math.min(1, plaqueProgress);

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: overlayOpacity }}>
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{ position: "absolute", inset: 0 }}
      >
        {/* Outer atmospheric glow */}
        <circle
          cx={cx} cy={cy} r={OUTER_R + 32}
          fill="rgba(160,18,8,0.20)"
          style={{ filter: "blur(22px)" }}
        />

        {/* Vessel wall fill */}
        <circle cx={cx} cy={cy} r={OUTER_R} fill="rgba(48,6,6,0.90)" />

        {/* Vessel wall border */}
        <circle
          cx={cx} cy={cy} r={OUTER_R}
          fill="none" stroke="rgba(210,55,32,0.72)" strokeWidth={3.5}
        />

        {/* Inner wall lining (endothelium) */}
        <circle
          cx={cx} cy={cy} r={INNER_WALL_R}
          fill="none" stroke="rgba(230,85,55,0.30)" strokeWidth={1.2}
        />

        {/* Plaque deposits — grow from wall inward */}
        {DEPOSITS.map((dep, i) => {
          const depP = Math.max(0, Math.min(1, (p3 - dep.delay) / Math.max(0.001, 1 - dep.delay)));
          const maxThick = dep.maxFrac * (INNER_WALL_R - minLumen);
          const thickness = maxThick * depP;
          if (thickness < 2) return null;
          const pInner = Math.max(lumenR, INNER_WALL_R - thickness);
          return (
            <g key={i}>
              {/* Soft outer halo of deposit */}
              <path
                d={arcPath(cx, cy, Math.max(lumenR, INNER_WALL_R - thickness * 1.15), INNER_WALL_R, dep.start, dep.span)}
                fill={`rgba(170,115,22,${0.28 + depP * 0.18})`}
                style={{ filter: "blur(4px)" }}
              />
              {/* Plaque body */}
              <path
                d={arcPath(cx, cy, pInner, INNER_WALL_R, dep.start, dep.span)}
                fill={`rgba(198,150,38,${0.52 + depP * 0.30})`}
              />
            </g>
          );
        })}

        {/* Blood-filled lumen */}
        <circle cx={cx} cy={cy} r={lumenR} fill="rgba(148,16,16,0.55)" />

        {/* Inner lumen glow — brightens as narrowing intensifies (danger signal) */}
        <circle
          cx={cx} cy={cy} r={lumenR * 0.65}
          fill="rgba(200,28,28,0.30)"
          style={{ filter: "blur(6px)" }}
        />

        {/* Lumen boundary — glows redder as stenosis increases */}
        <circle
          cx={cx} cy={cy} r={lumenR}
          fill="none"
          stroke={`rgba(240,72,48,${0.42 + plaqueProgress * 0.28})`}
          strokeWidth={2}
        />

        {/* Dashed reference ring — signals this is a medical cross-section */}
        <circle
          cx={cx} cy={cy} r={OUTER_R + 14}
          fill="none"
          stroke="rgba(240,145,90,0.20)"
          strokeWidth={1}
          strokeDasharray="9 5"
        />
      </svg>
    </AbsoluteFill>
  );
};
