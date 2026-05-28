import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

// Each silhouette appears during the first ~43% of the video
// (the "things you do every day" opening narration)
// Positioned at the vignette-darkened edges so the doctor stays readable

interface SceneDef {
  key:        string;
  startFrac:  number;
  endFrac:    number;
  cx:         number; // center x as % of width
  cy:         number; // center y as % of height
  driftDx:    number; // horizontal parallax drift in px over display window
  flipX?:     boolean;
}

const SCENES: SceneDef[] = [
  { key: "smoking",  startFrac: 0.040, endFrac: 0.200, cx: 14, cy: 22, driftDx: -10 },
  { key: "drinking", startFrac: 0.088, endFrac: 0.256, cx: 87, cy: 20, driftDx:  10, flipX: true },
  { key: "food",     startFrac: 0.142, endFrac: 0.312, cx: 11, cy: 68, driftDx:  -8 },
  { key: "sitting",  startFrac: 0.192, endFrac: 0.368, cx: 89, cy: 66, driftDx:   8, flipX: true },
  { key: "stressed", startFrac: 0.248, endFrac: 0.415, cx: 50, cy: 91, driftDx:   5 },
];

const FIG_W = 162;
const FIG_H = 248;

// ── SVG figure definitions, viewBox "0 0 100 180" ───────────────────────────
// All shapes use fill="currentColor" / stroke="currentColor"
// so the outer <svg> color prop drives the silhouette shade.

const SmokingFig: React.FC = () => (
  <g>
    <circle cx="50" cy="16" r="14" />
    <rect x="44" y="29" width="12" height="9" rx="4" />
    <path d="M30 38 Q18 65 20 100 Q20 112 50 114 Q80 112 80 100 Q82 65 70 38 Z" />
    {/* Left arm hanging */}
    <path d="M30 52 Q16 66 14 93" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    {/* Right arm raised — cigarette at lip */}
    <path d="M70 52 Q80 44 84 33" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    {/* Cigarette stick */}
    <rect x="82" y="24" width="4" height="14" rx="2" />
    {/* Lit glow */}
    <circle cx="84" cy="24" r="2.8" fill="rgba(255,145,40,0.85)" />
    {/* Smoke wisps */}
    <path d="M86 21 C83 12 89 6 86 -2" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" fill="none" opacity={0.52} />
    <path d="M89 19 C93 10 89 3 93 -3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" fill="none" opacity={0.36} />
    {/* Legs */}
    <path d="M37 114 Q35 138 33 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
    <path d="M63 114 Q65 138 67 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
  </g>
);

const FastFoodFig: React.FC = () => (
  <g>
    <circle cx="50" cy="16" r="14" />
    <rect x="44" y="29" width="12" height="9" rx="4" />
    <path d="M30 38 Q18 65 20 100 Q20 112 50 114 Q80 112 80 100 Q82 65 70 38 Z" />
    {/* Left arm hanging */}
    <path d="M30 52 Q16 66 14 93" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    {/* Right arm raised — food at mouth */}
    <path d="M70 52 Q80 46 84 36" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    {/* Burger body */}
    <ellipse cx="89" cy="29" rx="9" ry="6" />
    {/* Bun dome on top */}
    <path d="M82 26 Q89 17 96 26" fill="currentColor" />
    {/* Legs */}
    <path d="M37 114 Q35 138 33 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
    <path d="M63 114 Q65 138 67 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
  </g>
);

const SittingFig: React.FC = () => (
  <g>
    <circle cx="50" cy="15" r="14" />
    <rect x="44" y="28" width="12" height="9" rx="4" />
    {/* Torso, slightly forward lean */}
    <path d="M30 37 Q18 64 20 99 Q20 111 50 113 Q80 111 80 99 Q82 64 70 37 Z" />
    {/* Chair back */}
    <rect x="78" y="36" width="6" height="77" rx="3" />
    {/* Chair seat */}
    <rect x="8" y="111" width="70" height="6" rx="3" />
    {/* Arms on armrests */}
    <path d="M30 54 Q15 59 10 69 Q10 84 14 86" stroke="currentColor" strokeWidth="10" strokeLinecap="round" fill="none" />
    <path d="M70 54 Q85 59 90 69 Q90 84 86 86" stroke="currentColor" strokeWidth="10" strokeLinecap="round" fill="none" />
    {/* Upper legs (thighs, horizontal) */}
    <path d="M35 117 Q33 131 33 144" stroke="currentColor" strokeWidth="14" strokeLinecap="round" fill="none" />
    <path d="M65 117 Q67 131 67 144" stroke="currentColor" strokeWidth="14" strokeLinecap="round" fill="none" />
    {/* Lower legs (forward, resting on floor) */}
    <path d="M33 144 Q21 148 11 148" stroke="currentColor" strokeWidth="12" strokeLinecap="round" fill="none" />
    <path d="M67 144 Q79 148 89 148" stroke="currentColor" strokeWidth="12" strokeLinecap="round" fill="none" />
  </g>
);

const StressedFig: React.FC = () => (
  <g>
    <circle cx="50" cy="16" r="14" />
    <rect x="44" y="29" width="12" height="9" rx="4" />
    <path d="M30 38 Q18 65 20 100 Q20 112 50 114 Q80 112 80 100 Q82 65 70 38 Z" />
    {/* Left arm up — elbow out — hand on temple */}
    <path d="M30 52 Q14 44 12 32 Q12 24 21 23" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    {/* Right arm up — elbow out — hand on temple */}
    <path d="M70 52 Q86 44 88 32 Q88 24 79 23" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    {/* Stress marks above head */}
    <path d="M37 7 L33 0"  stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" fill="none" />
    <path d="M50 5 L50 -2" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" fill="none" />
    <path d="M63 7 L67 0"  stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" fill="none" />
    {/* Legs */}
    <path d="M37 114 Q35 138 33 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
    <path d="M63 114 Q65 138 67 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
  </g>
);

const DrinkingFig: React.FC = () => (
  <g>
    <circle cx="50" cy="16" r="14" />
    <rect x="44" y="29" width="12" height="9" rx="4" />
    <path d="M30 38 Q18 65 20 100 Q20 112 50 114 Q80 112 80 100 Q82 65 70 38 Z" />
    {/* Left arm hanging */}
    <path d="M30 52 Q16 66 14 93" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    {/* Right arm raised — cup at mouth */}
    <path d="M70 52 Q80 45 83 34" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    {/* Cup (trapezoid) */}
    <path d="M79 25 L78 41 L93 41 L92 25 Z" />
    <line x1="79" y1="25" x2="92" y2="25" stroke="currentColor" strokeWidth="2" />
    {/* Straw */}
    <path d="M88 25 Q89 17 91 9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" fill="none" />
    {/* Legs */}
    <path d="M37 114 Q35 138 33 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
    <path d="M63 114 Q65 138 67 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
  </g>
);

// ── Main component ───────────────────────────────────────────────────────────

export const SilhouetteOverlay: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {SCENES.map((scene) => {
        const startF = Math.round(scene.startFrac * durationInFrames);
        const endF   = Math.round(scene.endFrac   * durationInFrames);
        const FADE   = 18;

        // Quick visibility check before computing opacity
        if (frame < startF - FADE || frame > endF + FADE) return null;

        const opacity = interpolate(
          frame,
          [startF - FADE, startF, endF, endF + FADE],
          [0, 0.50, 0.50, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );
        if (opacity < 0.004) return null;

        const progress = Math.max(0, Math.min(1, (frame - startF) / Math.max(1, endF - startF)));
        const driftX   = progress * scene.driftDx;

        const cx   = (scene.cx / 100) * width;
        const cy   = (scene.cy / 100) * height;
        const left = cx - FIG_W / 2 + driftX;
        const top  = cy - FIG_H / 2;

        return (
          <div
            key={scene.key}
            style={{
              position: "absolute",
              left,
              top,
              width: FIG_W,
              height: FIG_H,
              opacity,
              overflow: "visible",
            }}
          >
            {/* Warm amber backlight halo — cinematic back-lighting */}
            <div
              style={{
                position: "absolute",
                inset: -20,
                background:
                  "radial-gradient(ellipse at 50% 75%, rgba(210,115,28,0.28) 0%, rgba(140,60,10,0.12) 45%, transparent 72%)",
                filter: "blur(12px)",
                pointerEvents: "none",
              }}
            />
            {/* Silhouette SVG figure */}
            <svg
              viewBox="0 0 100 180"
              width={FIG_W}
              height={FIG_H}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                color: "rgba(8, 4, 2, 0.92)",
                ...(scene.flipX
                  ? { transform: "scaleX(-1)", transformOrigin: "50% 50%" }
                  : {}),
              }}
            >
              {scene.key === "smoking"  && <SmokingFig  />}
              {scene.key === "food"     && <FastFoodFig />}
              {scene.key === "sitting"  && <SittingFig  />}
              {scene.key === "stressed" && <StressedFig />}
              {scene.key === "drinking" && <DrinkingFig />}
            </svg>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
