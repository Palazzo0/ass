import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

// SVG feTurbulence with per-frame seed = different noise every frame → film grain
export const FilmGrain: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const seed = frame % 997; // prime keeps it varied without overflow

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <svg
        width={width}
        height={height}
        style={{ position: "absolute", inset: 0 }}
      >
        <defs>
          <filter id={`fg-${seed}`} x="0%" y="0%" width="100%" height="100%">
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.80"
              numOctaves="4"
              seed={seed}
              stitchTiles="stitch"
              result="noise"
            />
            <feColorMatrix
              in="noise"
              type="saturate"
              values="0"
              result="grey"
            />
            <feBlend in="SourceGraphic" in2="grey" mode="overlay" result="blended" />
            <feComponentTransfer in="blended">
              <feFuncA type="linear" slope="0.045" />
            </feComponentTransfer>
          </filter>
        </defs>
        <rect
          x={0}
          y={0}
          width={width}
          height={height}
          filter={`url(#fg-${seed})`}
          fill="white"
        />
      </svg>
    </AbsoluteFill>
  );
};
