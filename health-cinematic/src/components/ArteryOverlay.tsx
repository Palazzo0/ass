import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import {
  PHASE_1_END,
  PHASE_2_END,
  PHASE_3_END,
  getPhaseProgress,
} from "../utils/phases";

// Beat-pulse helper — returns 0-1 matching lub-dub rhythm
const BEAT_FRAMES = 36;
function beatPulse(frame: number): number {
  const ph = (frame % BEAT_FRAMES) / BEAT_FRAMES;
  if (ph < 0.14) return interpolate(ph, [0, 0.07, 0.14], [0, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (ph >= 0.50 && ph < 0.62) return interpolate(ph, [0.50, 0.56, 0.62], [0, 0.55, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return 0;
}

// pathLength="1" trick: dashArray={`${d} ${1-d}`} reveals path 0→d from start
const drawDash = (d: number) => `${Math.max(0.0001, d).toFixed(5)} ${Math.max(0.0001, 1 - d + 0.0001).toFixed(5)}`;

const PATHS = {
  // Main descending vessels (left + right frame edges)
  mainRight: "M 985 0 C 962 280 1005 560 980 840 C 955 1120 935 1400 948 1920",
  mainLeft:  "M 95 0 C 118 280 75 560 100 840 C 125 1120 148 1400 135 1920",
  // Branches from right vessel
  brR1: "M 968 280 C 920 310 872 330 820 352 C 768 374 720 390 672 400",
  brR2: "M 955 630 C 898 668 840 706 782 748 C 724 790 678 832 648 872",
  brR3: "M 962 440 C 915 466 872 492 834 522",
  // Branches from left vessel
  brL1: "M 108 260 C 162 295 218 320 274 344 C 330 368 386 386 432 398",
  brL2: "M 122 590 C 185 628 248 668 312 710 C 376 752 428 794 460 836",
  brL3: "M 115 410 C 165 436 212 462 254 492",
  // Bottom capillary network
  cap1: "M 185 1720 C 300 1700 430 1718 560 1730 C 688 1742 808 1728 912 1712",
  cap2: "M 340 1768 C 418 1784 496 1774 574 1764 C 652 1754 728 1769 804 1759",
  capR: "M 795 1615 C 838 1638 866 1668 882 1700 C 898 1732 900 1762 884 1792",
};

export const ArteryOverlay: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();

  const p1 = getPhaseProgress(frame, durationInFrames, 0, PHASE_1_END);
  const p2 = getPhaseProgress(frame, durationInFrames, 0.38, PHASE_2_END);
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, PHASE_3_END);
  const beat = beatPulse(frame);

  // Phase 1: arteries draw themselves progressively (scan effect)
  const drawProgress = interpolate(p1, [0, 0.75], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Global opacity arc
  const globalOpacity =
    interpolate(p1, [0, 0.2, 1], [0, 0.55, 0.82], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) +
    interpolate(p2, [0, 0.5, 1], [0, 0.12, 0.20], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) +
    interpolate(p3, [0, 1], [0, -0.15], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Stroke widths: broaden in phase 2, dramatically narrow in phase 3
  const narrowFactor = interpolate(p3, [0, 0.5, 1], [1, 0.50, 0.14], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const mainW   = (4.5 + interpolate(p2, [0, 1], [0, 1.4], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })) * narrowFactor;
  const branchW = (2.5 + interpolate(p2, [0, 1], [0, 0.8], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })) * narrowFactor;

  // Color: dark red → bright alert red in phase 2 → bruised purple-dark in phase 3
  const redR   = Math.round(interpolate(p2, [0, 1], [188, 235], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const redG   = Math.round(interpolate(p3, [0, 1], [48, 18], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const redA   = interpolate(p2, [0, 1], [0.42, 0.72], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Glow: beat-synced pulse in phase 2
  const baseGlow = interpolate(p2, [0, 0.3, 1], [0, 0.22, 0.32], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glowA = Math.max(0, baseGlow + beat * interpolate(p2, [0, 1], [0, 0.22], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));

  // Plaque / blockage fill growing in phase 3
  const plaqueA = interpolate(p3, [0, 0.5, 1], [0, 0.55, 0.88], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const mainDash   = drawDash(drawProgress);
  const branchDash = drawDash(interpolate(p1, [0.05, 0.80], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const capDash    = drawDash(interpolate(p1, [0.15, 0.95], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));

  const stroke = `rgba(${redR},${redG},45,${redA})`;
  const brStroke = `rgba(155,38,38,${redA * 0.82})`;

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: Math.max(0, globalOpacity) }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute", inset: 0 }}>

        {/* ── Glow halos on main vessels ── */}
        {[PATHS.mainRight, PATHS.mainLeft].map((d, i) => (
          <path key={`glow-${i}`} d={d} fill="none"
            pathLength={1} strokeDasharray={mainDash} strokeDashoffset={0}
            stroke={`rgba(255,45,25,${glowA})`}
            strokeWidth={mainW * 4}
            strokeLinecap="round"
            style={{ filter: "blur(10px)" }}
          />
        ))}

        {/* ── Main descending vessels ── */}
        {[PATHS.mainRight, PATHS.mainLeft].map((d, i) => (
          <path key={`main-${i}`} d={d} fill="none"
            pathLength={1} strokeDasharray={mainDash} strokeDashoffset={0}
            stroke={stroke}
            strokeWidth={mainW}
            strokeLinecap="round"
          />
        ))}

        {/* ── Branch vessels ── */}
        {[PATHS.brR1, PATHS.brR2, PATHS.brR3, PATHS.brL1, PATHS.brL2, PATHS.brL3].map((d, i) => (
          <path key={`br-${i}`} d={d} fill="none"
            pathLength={1} strokeDasharray={branchDash} strokeDashoffset={0}
            stroke={brStroke}
            strokeWidth={branchW}
            strokeLinecap="round"
          />
        ))}

        {/* ── Fine capillaries ── */}
        {[PATHS.cap1, PATHS.cap2, PATHS.capR].map((d, i) => (
          <path key={`cap-${i}`} d={d} fill="none"
            pathLength={1} strokeDasharray={capDash} strokeDashoffset={0}
            stroke="rgba(130,35,35,0.32)"
            strokeWidth={1.4}
            strokeLinecap="round"
          />
        ))}

        {/* ── Plaque / blockage overlay (dark centre fill) ── */}
        {[PATHS.mainRight, PATHS.mainLeft].map((d, i) => (
          <path key={`plaque-${i}`} d={d} fill="none"
            pathLength={1} strokeDasharray={mainDash} strokeDashoffset={0}
            stroke={`rgba(8,0,0,${plaqueA})`}
            strokeWidth={mainW * 0.62}
            strokeLinecap="round"
          />
        ))}

        {/* ── Phase 3: branch occlusion (branches fade to near-invisible) ── */}
        {[PATHS.brR2, PATHS.brR3, PATHS.brL2, PATHS.brL3].map((d, i) => (
          <path key={`occlude-${i}`} d={d} fill="none"
            pathLength={1} strokeDasharray={branchDash} strokeDashoffset={0}
            stroke={`rgba(4,0,0,${plaqueA * 0.75})`}
            strokeWidth={branchW * 0.55}
            strokeLinecap="round"
          />
        ))}
      </svg>
    </AbsoluteFill>
  );
};
