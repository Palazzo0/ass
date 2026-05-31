import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

// Lifestyle silhouette figures — appear during Phase 2 (22–58% of video)
// Timed to the narration about habits that damage blood vessels.
// Positioned in vignette-darkened edge zones so the doctor stays readable.

interface SceneDef {
  key:       string;
  startFrac: number;
  endFrac:   number;
  cx:        number; // center x as % of width
  cy:        number; // center y as % of height
  driftDx:   number; // horizontal parallax drift in px
  flipX?:    boolean;
}

const SCENES: SceneDef[] = [
  { key: "sitting",      startFrac: 0.22, endFrac: 0.32, cx: 89, cy: 66, driftDx:  8, flipX: true },
  { key: "smoking",      startFrac: 0.24, endFrac: 0.34, cx: 14, cy: 22, driftDx: -10 },
  { key: "food",         startFrac: 0.30, endFrac: 0.40, cx: 87, cy: 20, driftDx:  10, flipX: true },
  { key: "hypertension", startFrac: 0.36, endFrac: 0.46, cx: 11, cy: 68, driftDx:  -8 },
  { key: "medication",   startFrac: 0.42, endFrac: 0.52, cx: 88, cy: 22, driftDx:   8, flipX: true },
  { key: "inflammation", startFrac: 0.48, endFrac: 0.58, cx: 50, cy: 91, driftDx:   5 },
];

const FIG_W = 162;
const FIG_H = 248;

// ── SVG figure definitions ───────────────────────────────────────────────────
// viewBox "0 0 100 180" — all shapes use fill/stroke="currentColor"

const SmokingFig: React.FC = () => (
  <g>
    <circle cx="50" cy="16" r="14" />
    <rect x="44" y="29" width="12" height="9" rx="4" />
    <path d="M30 38 Q18 65 20 100 Q20 112 50 114 Q80 112 80 100 Q82 65 70 38 Z" />
    <path d="M30 52 Q16 66 14 93" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    <path d="M70 52 Q80 44 84 33" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    <rect x="82" y="24" width="4" height="14" rx="2" />
    <circle cx="84" cy="24" r="2.8" fill="rgba(255,145,40,0.85)" />
    <path d="M86 21 C83 12 89 6 86 -2" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" fill="none" opacity={0.52} />
    <path d="M89 19 C93 10 89 3 93 -3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" fill="none" opacity={0.36} />
    <path d="M37 114 Q35 138 33 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
    <path d="M63 114 Q65 138 67 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
  </g>
);

const FastFoodFig: React.FC = () => (
  <g>
    <circle cx="50" cy="16" r="14" />
    <rect x="44" y="29" width="12" height="9" rx="4" />
    <path d="M30 38 Q18 65 20 100 Q20 112 50 114 Q80 112 80 100 Q82 65 70 38 Z" />
    <path d="M30 52 Q16 66 14 93" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    <path d="M70 52 Q80 46 84 36" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    <ellipse cx="89" cy="29" rx="9" ry="6" />
    <path d="M82 26 Q89 17 96 26" fill="currentColor" />
    <path d="M37 114 Q35 138 33 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
    <path d="M63 114 Q65 138 67 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
  </g>
);

const SittingFig: React.FC = () => (
  <g>
    <circle cx="50" cy="15" r="14" />
    <rect x="44" y="28" width="12" height="9" rx="4" />
    <path d="M30 37 Q18 64 20 99 Q20 111 50 113 Q80 111 80 99 Q82 64 70 37 Z" />
    <rect x="78" y="36" width="6" height="77" rx="3" />
    <rect x="8" y="111" width="70" height="6" rx="3" />
    <path d="M30 54 Q15 59 10 69 Q10 84 14 86" stroke="currentColor" strokeWidth="10" strokeLinecap="round" fill="none" />
    <path d="M70 54 Q85 59 90 69 Q90 84 86 86" stroke="currentColor" strokeWidth="10" strokeLinecap="round" fill="none" />
    <path d="M35 117 Q33 131 33 144" stroke="currentColor" strokeWidth="14" strokeLinecap="round" fill="none" />
    <path d="M65 117 Q67 131 67 144" stroke="currentColor" strokeWidth="14" strokeLinecap="round" fill="none" />
    <path d="M33 144 Q21 148 11 148" stroke="currentColor" strokeWidth="12" strokeLinecap="round" fill="none" />
    <path d="M67 144 Q79 148 89 148" stroke="currentColor" strokeWidth="12" strokeLinecap="round" fill="none" />
  </g>
);

const HypertensionFig: React.FC = () => (
  <g>
    <circle cx="50" cy="16" r="14" />
    <rect x="44" y="29" width="12" height="9" rx="4" />
    <path d="M30 38 Q18 65 20 100 Q20 112 50 114 Q80 112 80 100 Q82 65 70 38 Z" />
    {/* Both arms raised, gripping head in tension */}
    <path d="M30 52 Q15 46 13 34 Q12 24 22 22" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    <path d="M70 52 Q85 46 87 34 Q88 24 78 22" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    {/* Pressure burst lines above head */}
    <path d="M34 4 L28 -5"  stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" fill="none" />
    <path d="M50 2 L50 -7"  stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" fill="none" />
    <path d="M66 4 L72 -5"  stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" fill="none" />
    <path d="M26 10 L17 5"  stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" fill="none" />
    <path d="M74 10 L83 5"  stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" fill="none" />
    {/* Pulsing vein on temple */}
    <path d="M28 18 Q24 16 25 21 Q26 25 30 23" stroke="rgba(210,45,20,0.75)" strokeWidth="2.2" fill="none" strokeLinecap="round" />
    <path d="M72 18 Q76 16 75 21 Q74 25 70 23" stroke="rgba(210,45,20,0.75)" strokeWidth="2.2" fill="none" strokeLinecap="round" />
    {/* Legs */}
    <path d="M37 114 Q35 138 33 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
    <path d="M63 114 Q65 138 67 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
  </g>
);

const MedicationFig: React.FC = () => (
  <g>
    <circle cx="50" cy="16" r="14" />
    <rect x="44" y="29" width="12" height="9" rx="4" />
    <path d="M30 38 Q18 65 20 100 Q20 112 50 114 Q80 112 80 100 Q82 65 70 38 Z" />
    {/* Left arm raised, holding pill bottle out */}
    <path d="M30 52 Q20 56 16 68 Q14 78 18 84" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    {/* Right arm hanging at side */}
    <path d="M70 52 Q84 66 86 93" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    {/* Pill bottle in left hand */}
    <rect x="7" y="75" width="13" height="20" rx="3" fill="currentColor" />
    {/* Bottle cap */}
    <rect x="6" y="71" width="15" height="7" rx="3" fill="currentColor" />
    {/* Medicine cross on bottle */}
    <line x1="13.5" y1="80" x2="13.5" y2="90" stroke="rgba(235,235,235,0.62)" strokeWidth="2.2" />
    <line x1="9"    y1="85" x2="18"   y2="85" stroke="rgba(235,235,235,0.62)" strokeWidth="2.2" />
    {/* Legs */}
    <path d="M37 114 Q35 138 33 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
    <path d="M63 114 Q65 138 67 164" stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none" />
  </g>
);

const InflammationFig: React.FC = () => (
  <g>
    <circle cx="50" cy="16" r="14" />
    <rect x="44" y="29" width="12" height="9" rx="4" />
    <path d="M30 38 Q18 65 20 100 Q20 112 50 114 Q80 112 80 100 Q82 65 70 38 Z" />
    {/* Both arms crossed over chest/vessels */}
    <path d="M30 52 Q42 62 52 70" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    <path d="M70 52 Q58 62 48 70" stroke="currentColor" strokeWidth="11" strokeLinecap="round" fill="none" />
    {/* Inflammation hot-spots on chest */}
    <circle cx="42" cy="74" r="5" fill="rgba(225,55,28,0.68)" />
    <circle cx="59" cy="70" r="3.8" fill="rgba(225,55,28,0.52)" />
    <circle cx="50" cy="83" r="3.2" fill="rgba(225,55,28,0.44)" />
    {/* Radiating heat lines */}
    <path d="M42 68 L42 62" stroke="rgba(225,60,28,0.55)" strokeWidth="1.8" strokeLinecap="round" fill="none" />
    <path d="M36 74 L30 74" stroke="rgba(225,60,28,0.55)" strokeWidth="1.8" strokeLinecap="round" fill="none" />
    <path d="M48 74 L54 74" stroke="rgba(225,60,28,0.55)" strokeWidth="1.8" strokeLinecap="round" fill="none" />
    <path d="M38 69 L34 65" stroke="rgba(225,60,28,0.42)" strokeWidth="1.5" strokeLinecap="round" fill="none" />
    <path d="M46 69 L50 65" stroke="rgba(225,60,28,0.42)" strokeWidth="1.5" strokeLinecap="round" fill="none" />
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
            {/* Warm amber backlight halo */}
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
              {scene.key === "smoking"      && <SmokingFig      />}
              {scene.key === "food"         && <FastFoodFig     />}
              {scene.key === "sitting"      && <SittingFig      />}
              {scene.key === "hypertension" && <HypertensionFig />}
              {scene.key === "medication"   && <MedicationFig   />}
              {scene.key === "inflammation" && <InflammationFig />}
            </svg>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
