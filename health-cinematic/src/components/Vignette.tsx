import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export const Vignette: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  // Slowly breathe: very subtle opacity oscillation
  const breathe = Math.sin((frame / fps) * 0.4) * 0.015;

  // Base opacity ramps up slightly toward end for dramatic tension
  const baseOpacity = interpolate(
    frame,
    [0, durationInFrames * 0.6, durationInFrames],
    [0.55, 0.58, 0.68],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const opacity = baseOpacity + breathe;

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(ellipse at 50% 45%, transparent 30%, rgba(0,0,0,0.7) 80%, rgba(0,0,0,0.92) 100%)",
        opacity,
        pointerEvents: "none",
      }}
    />
  );
};
