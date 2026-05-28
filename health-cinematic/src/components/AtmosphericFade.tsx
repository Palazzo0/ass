import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PHASE_2_END, PHASE_3_END, getPhaseProgress } from "../utils/phases";

export const AtmosphericFade: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  // Fade in from black
  const fadeIn = interpolate(frame, [0, fps * 1.0], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Fade out to black
  const fadeOut = interpolate(
    frame,
    [durationInFrames - fps * 2.2, durationInFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const blackOpacity = Math.max(fadeIn, fadeOut);

  // Warm amber grade (subtle, cinematic)
  const warmGrade = interpolate(frame, [0, fps * 1.2], [0, 0.045], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Phase 3: deeper atmospheric dark layer + cool desaturation
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, PHASE_3_END);
  const shadowLayer = interpolate(p3, [0, 1], [0, 0.38], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Cool blue-grey desaturation tint — "life draining" feeling
  const coolTint = interpolate(p3, [0, 0.4, 1], [0, 0.05, 0.14], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Warm tone grade */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(70, 25, 0, 1)",
          opacity: warmGrade,
          mixBlendMode: "multiply" as const,
        }}
      />
      {/* Phase 3 heavy shadow */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.7) 100%)",
          opacity: shadowLayer,
        }}
      />
      {/* Phase 3 cool desaturation tint */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(20, 30, 55, 1)",
          opacity: coolTint,
          mixBlendMode: "multiply" as const,
        }}
      />
      {/* Black fade in/out */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "#000",
          opacity: blackOpacity,
        }}
      />
    </AbsoluteFill>
  );
};
