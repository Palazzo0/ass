import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import {
  PHASE_1_END,
  PHASE_2_END,
  PHASE_3_END,
  getPhaseProgress,
} from "../utils/phases";

const BEAT_FRAMES = 36;
function beatPulse(frame: number): number {
  const phase = (frame % BEAT_FRAMES) / BEAT_FRAMES;
  if (phase < 0.14) return interpolate(phase, [0, 0.07, 0.14], [0, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (phase >= 0.5 && phase < 0.62) return interpolate(phase, [0.5, 0.56, 0.62], [0, 0.55, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return 0;
}

const ARTERY_PATHS = [
  // Main right descending vessel
  "M 960 0 C 940 200 980 400 960 600 C 940 800 920 1000 900 1200 C 880 1400 860 1600 870 1920",
  // Right branch 1
  "M 940 350 C 900 380 860 400 820 430 C 780 460 740 490 700 510",
  // Right branch 2
  "M 920 700 C 870 730 820 760 770 800 C 720 840 680 880 650 920",
  // Right small branch
  "M 895 520 C 855 545 820 570 790 600",
  // Left descending vessel
  "M 120 0 C 140 200 100 400 120 600 C 140 800 160 1000 180 1200 C 200 1400 220 1600 210 1920",
  // Left branch 1
  "M 140 300 C 190 340 240 370 290 400 C 340 430 390 450 430 470",
  // Left branch 2
  "M 160 650 C 220 690 280 730 340 770 C 400 810 450 850 480 890",
  // Bottom capillary network
  "M 200 1700 C 300 1680 400 1700 540 1720 C 660 1740 780 1730 900 1710",
  "M 350 1750 C 420 1770 490 1760 560 1750 C 630 1740 700 1755 770 1745",
  // Lower right cluster
  "M 780 1600 C 820 1620 850 1650 870 1680 C 890 1710 895 1740 880 1770",
  "M 830 1640 C 860 1655 880 1670 895 1700",
];

export const ArteryOverlay: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();

  const p1 = getPhaseProgress(frame, durationInFrames, 0, PHASE_1_END);
  const p2 = getPhaseProgress(frame, durationInFrames, 0.38, PHASE_2_END);
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, PHASE_3_END);

  const beat = beatPulse(frame);

  // Phase 1: arteries emerge gradually
  const phase1Opacity = interpolate(p1, [0, 0.25, 1], [0, 0.55, 0.82], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Phase 2: become more vivid and glowing
  const phase2Boost = interpolate(p2, [0, 0.5, 1], [0, 0.18, 0.25], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Phase 3: stay visible but darken
  const phase3Shift = interpolate(p3, [0, 1], [0, -0.12], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const globalOpacity = Math.max(0, phase1Opacity + phase2Boost + phase3Shift);

  // Stroke width — narrows dramatically in phase 3
  const narrowProgress = interpolate(p3, [0, 0.6, 1], [1, 0.45, 0.18], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const mainStroke   = (4.0 + interpolate(p2, [0, 1], [0, 1.2], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })) * narrowProgress;
  const branchStroke = (2.2 + interpolate(p2, [0, 1], [0, 0.6], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })) * narrowProgress;

  // Color: warm red → bright red in phase 2 → dark in phase 3
  const redR = Math.round(interpolate(p2, [0, 1], [185, 228], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const redA = interpolate(p2, [0, 1], [0.40, 0.65], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Glow — beat-synced in phase 2
  const baseGlow = interpolate(p2, [0, 0.4, 1], [0, 0.20, 0.28], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glowOpacity = baseGlow + beat * interpolate(p2, [0, 1], [0, 0.18], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Plaque darkening in phase 3
  const plaqueOpacity = interpolate(p3, [0, 0.7, 1], [0, 0.55, 0.80], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: globalOpacity }}>
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{ position: "absolute", inset: 0 }}
      >
        {/* Glow layer behind main vessels */}
        {[0, 4].map((idx) => (
          <path
            key={`glow-${idx}`}
            d={ARTERY_PATHS[idx]}
            fill="none"
            stroke={`rgba(255,60,60,${glowOpacity})`}
            strokeWidth={mainStroke * 3.5}
            strokeLinecap="round"
            style={{ filter: "blur(8px)" }}
          />
        ))}

        {/* Main vessels */}
        {[0, 4].map((idx) => (
          <path
            key={`main-${idx}`}
            d={ARTERY_PATHS[idx]}
            fill="none"
            stroke={`rgba(${redR},50,50,${redA})`}
            strokeWidth={mainStroke}
            strokeLinecap="round"
          />
        ))}

        {/* Branches */}
        {[1, 2, 3, 5, 6].map((idx) => (
          <path
            key={`branch-${idx}`}
            d={ARTERY_PATHS[idx]}
            fill="none"
            stroke={`rgba(160,45,45,${redA * 0.8})`}
            strokeWidth={branchStroke}
            strokeLinecap="round"
          />
        ))}

        {/* Fine capillaries */}
        {[7, 8, 9, 10].map((idx) => (
          <path
            key={`cap-${idx}`}
            d={ARTERY_PATHS[idx]}
            fill="none"
            stroke="rgba(140,40,40,0.30)"
            strokeWidth={1.2}
            strokeLinecap="round"
          />
        ))}

        {/* Plaque blockage overlay */}
        {[0, 4].map((idx) => (
          <path
            key={`plaque-${idx}`}
            d={ARTERY_PATHS[idx]}
            fill="none"
            stroke={`rgba(15,5,5,${plaqueOpacity})`}
            strokeWidth={mainStroke * 0.55}
            strokeLinecap="round"
          />
        ))}
      </svg>
    </AbsoluteFill>
  );
};
