import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PHASE_1_END, PHASE_2_END, PHASE_3_END, getPhaseProgress } from "../utils/phases";

export const AtmosphericFade: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  // Fade in from black (1 s)
  const fadeIn = interpolate(frame, [0, fps], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Fade out to black (2.5 s)
  const fadeOut = interpolate(
    frame,
    [durationInFrames - fps * 2.5, durationInFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const blackOpacity = Math.max(fadeIn, fadeOut);

  // Phase 1: warm amber cinematic grade
  const p1 = getPhaseProgress(frame, durationInFrames, 0, PHASE_1_END);
  const warmGrade = interpolate(p1, [0, 1], [0, 0.055], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Phase 2: ambient red warmth
  const p2 = getPhaseProgress(frame, durationInFrames, 0.38, PHASE_2_END);
  const redWarm = interpolate(p2, [0, 0.5, 1], [0, 0.04, 0.06], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Phase 3: heavy shadow + blue-grey desaturation drain ("life leaving")
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, PHASE_3_END);
  const shadowLayer = interpolate(p3, [0, 0.3, 1], [0, 0.18, 0.42], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const coolTint = interpolate(p3, [0, 0.4, 1], [0, 0.06, 0.18], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Slow atmospheric blur pulse in phase 3 (simulated via opacity oscillation)
  const blurPulse = p3 > 0
    ? 0.02 * Math.sin(frame * 0.04) * p3
    : 0;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Warm amber grade (multiply, phase 1+) */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(72, 24, 0, 1)",
          opacity: warmGrade + redWarm,
          mixBlendMode: "multiply" as const,
        }}
      />
      {/* Phase 3 atmospheric shadow radial */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at 50% 48%, rgba(0,0,0,0.05) 0%, rgba(0,0,0,0.75) 100%)",
          opacity: shadowLayer + blurPulse,
        }}
      />
      {/* Phase 3 cool desaturation tint (multiply) */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(18, 28, 52, 1)",
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
