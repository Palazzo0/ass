import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export const AtmosphericFade: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  // Fade in from black over first ~1s
  const fadeInOpacity = interpolate(frame, [0, fps * 1.2], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Fade out to black over last ~2s
  const fadeOutOpacity = interpolate(
    frame,
    [durationInFrames - fps * 2.5, durationInFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const blackOpacity = Math.max(fadeInOpacity, fadeOutOpacity);

  // Warm cinematic grade — very subtle amber lift over mid-tones
  const warmGradeOpacity = interpolate(
    frame,
    [0, fps * 1.5, durationInFrames - fps * 2],
    [0, 0.04, 0.04],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Warm tone overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(80, 30, 0, 1)",
          opacity: warmGradeOpacity,
          mixBlendMode: "multiply" as const,
        }}
      />
      {/* Black fade */}
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
