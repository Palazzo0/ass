import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

// Artery SVG paths for a 1080x1920 canvas
// Positioned along edges and lower portion so as not to cover the face
const ARTERY_PATHS = [
  // Main right descending vessel (runs along right edge)
  "M 960 0 C 940 200 980 400 960 600 C 940 800 920 1000 900 1200 C 880 1400 860 1600 870 1920",
  // Right branch 1 (goes inward)
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
  // Bottom network near lower frame
  "M 200 1700 C 300 1680 400 1700 540 1720 C 660 1740 780 1730 900 1710",
  "M 350 1750 C 420 1770 490 1760 560 1750 C 630 1740 700 1755 770 1745",
  // Capillary cluster — lower right
  "M 780 1600 C 820 1620 850 1650 870 1680 C 890 1710 895 1740 880 1770",
  "M 830 1640 C 860 1655 880 1670 895 1700",
];

export const ArteryOverlay: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();

  // Global opacity: fades in slowly, stays, pulses slightly at end
  const globalOpacity = interpolate(
    frame,
    [0, 60, durationInFrames * 0.5, durationInFrames * 0.85, durationInFrames],
    [0, 0.55, 0.65, 0.75, 0.5],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Narrowing: stroke-width decreases toward end of video
  const strokeNarrow = interpolate(
    frame,
    [durationInFrames * 0.55, durationInFrames * 0.95],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const mainStrokeWidth = 1.2 + strokeNarrow * 0.6; // narrows from 1.8 → 1.2
  const branchStrokeWidth = 0.7 + strokeNarrow * 0.4;

  // Plaque build-up effect: dark fill gets more visible toward end
  const plaqueOpacity = interpolate(
    frame,
    [durationInFrames * 0.5, durationInFrames],
    [0, 0.55],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: globalOpacity }}>
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{ position: "absolute", inset: 0 }}
      >
        {/* Main vessels — thicker strokes */}
        {[0, 4].map((idx) => (
          <path
            key={`main-${idx}`}
            d={ARTERY_PATHS[idx]}
            fill="none"
            stroke="rgba(180,60,60,0.22)"
            strokeWidth={mainStrokeWidth}
            strokeLinecap="round"
          />
        ))}

        {/* Branches */}
        {[1, 2, 3, 5, 6].map((idx) => (
          <path
            key={`branch-${idx}`}
            d={ARTERY_PATHS[idx]}
            fill="none"
            stroke="rgba(160,50,50,0.18)"
            strokeWidth={branchStrokeWidth}
            strokeLinecap="round"
          />
        ))}

        {/* Fine capillaries */}
        {[7, 8, 9, 10].map((idx) => (
          <path
            key={`cap-${idx}`}
            d={ARTERY_PATHS[idx]}
            fill="none"
            stroke="rgba(150,50,50,0.14)"
            strokeWidth={0.5}
            strokeLinecap="round"
          />
        ))}

        {/* Plaque overlay: narrowed dark fill inside main arteries */}
        {[0, 4].map((idx) => (
          <path
            key={`plaque-${idx}`}
            d={ARTERY_PATHS[idx]}
            fill="none"
            stroke={`rgba(20,8,8,${plaqueOpacity * 0.6})`}
            strokeWidth={mainStrokeWidth * 0.5}
            strokeLinecap="round"
          />
        ))}
      </svg>
    </AbsoluteFill>
  );
};
